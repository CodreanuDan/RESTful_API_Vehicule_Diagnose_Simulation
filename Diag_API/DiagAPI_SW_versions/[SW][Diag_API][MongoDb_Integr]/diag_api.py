#***********************************************************************
# MODULE: diag_api
# SCOPE:  RESTful api made with flask-restful for communication with the virtual ecu trough TX and RX jsons.
# REV: 1.0
# REV: 2.0 - 
#
# Created by: Codreanu Dan
# Descr:
#***********************************************************************

#***********************************************************************
# IMPORTS:
from flask import Flask, request, jsonify
from flask_restful import Api, Resource

from Diag_API.key_generator import Key_Generator as key_gen
from Diag_API.settings_manager import SettingsManager as config
from Diag_API.ecu_communication_manager import EcuCommunicationManger as ecu_com_mng
from Diag_API.mongo_db_handler import MongoDBHandler, DATABASE_NAME, COLLECTION_NAME, CONNECTION_STRING
from Diag_API.diag_utils import Diag_DataBaseCom_Utils as db_con_utils

diag_api_app = Flask(__name__)
diag_api = Api(diag_api_app)


class Diag_API(Resource, key_gen, ecu_com_mng):
    """ 
        :Class name: Diag_API
        :Inherits from: Resource, Key_Generator, EcuCommunicationManger
        :Descr: Restful API used for communication between the virtual ecu and diag client
        :API Methods: GET, PUT
    """
    def __init__(self):
        """ """
        super().__init__()
        # Initalise communication with the virtual ecu
        ecu_com_mng.__init__(self)
        # API key is retrived from the .env file
        self.__API_KEY = config.get_api_key("API_KEY")
        # Main categories from the output json 
        self.valid_params = ['ign_stat',
                             'power_supply',
                             'engine_info',
                             'error_log',
                             'error_input',
                             'error_memory',
                             'can_handle_error_manager',
                             'clear_error_memory',
                             'clear_error_log',
                             'security_access',
                             'security_access',
                             'time_stamp',
                             'REAL_RPM']
        # valid_delete_params from the input json 
        self.valid_delete_params = ["error_injection",
                                    "clear_error_memory",
                                    "clear_error_log",
                                    "parameter_to_delete"]

    # *>>_____AUXILIARY_METHODS______________________________________________
    # ***********************************************************************

    def validate_api_key(self):
        """ 
            :Function name: get
            - Descr: Validate API key by comparing the key
                     from the client with the key stored in the .env file.
                     Used in all API methods as authetification is required.
            :return: dict, rc(401)  or None if success       
        """
        api_key = request.headers.get("x-api-key")
        # Strip "" from received key so we can compare 'key' to 'key'
        api_key = api_key.strip('"') if api_key else ''

        if api_key != self.__API_KEY:
            return {"message": "Unauthorized"}, 401
        return None  
    
    def get_sec_acc_calc_key(self, ecu_data: list) -> dict:
        """
            Extracts security_access data from ECU JSON and returns the seed and generated key.
        """
        try:
            data_to_return = ecu_data[0]  
            seed = data_to_return["security_access"].get("seed", 0) 
            print(f"seed: {seed}")
            key = self.KeyGen_genKey(seed=seed)
            return {"seed": seed, "key": key}, 200
        except KeyError:
            return {"message": "security_access not found in ECU data"}, 400
    
  
    # *>>_____API_METHODS____________________________________________________
    # ***********************************************************************

    ''' >>> GET  '''#___GET_METHOD___________________________________________________________
    def get(self) -> dict:
        """ 
            :Function name: get
            - Descr: Returns JSON data for the ECU with a specific parameter or whole info
                    if no parameter is specified in the request.
                    Equivalent for GET method, ~ GET data by <id>; as the id are the params from the json file.
            - Example request with param: GET: http://localhost:5000/ecu?param=engine_info.rpm -> returns param "rpm" from
                            engine info sub-category of output json. 
            - Example request with param: GET: http://localhost:5000/ecu -> returns all info from json.
            - Example request for snapshot: GET: http://localhost:5000/ecu?snapshot_id=20250504_2351 -> returns specific diagnostic snapshot
            - Example request for all snapshots: GET: http://localhost:5000/ecu?get_snapshots=true -> returns all stored snapshots
            :return: dict, rc
            :response codes: 200 OK, 400 Bad Request, 401 Unauthorized, 404 Not Found, 500 Server Error
        """
        # Validate API KEY return 401 if invalid
        validation_response = self.validate_api_key()
        if validation_response:
            return validation_response
        
        #*************************************************************************************
        # Added MongoDB snapshot retrieval functionality
        # Check if snapshot retrieval is requested
        snapshot_id = request.args.get('snapshot_id')
        get_snapshots = request.args.get('get_snapshots')
        
        if snapshot_id or get_snapshots:
            # Init connection to database
            self.mongo_db_handler = MongoDBHandler(uri=CONNECTION_STRING, db_name=DATABASE_NAME, collection_name=COLLECTION_NAME)
            
            if snapshot_id:
                # Get specific snapshot
                snapshot = self.mongo_db_handler.get_snapshot_data_from_db(snapshot_id)
                if snapshot:
                    # Convert MongoDB ObjectId to string for JSON serialization
                    if '_id' in snapshot:
                        snapshot['_id'] = str(snapshot['_id'])
                    return {"message": "Snapshot retrieved successfully", "data": snapshot}, 200
                else:
                    return {"message": f"No snapshot found with ID: {snapshot_id}"}, 404
            else:
                # Get all snapshots
                snapshots = self.mongo_db_handler.get_snapshot_data_from_db()
                if snapshots:
                    # Convert MongoDB ObjectIds to strings for JSON serialization
                    for snapshot in snapshots:
                        if '_id' in snapshot:
                            snapshot['_id'] = str(snapshot['_id'])
                    return {"message": "Snapshots retrieved successfully", "count": len(snapshots), "data": snapshots}, 200
                else:
                    return {"message": "Failed to retrieve snapshots or no snapshots found"}, 500
        #*************************************************************************************
        
        # URL paramter; what do you want to get from the api resource? 
        param = request.args.get('param', None)

        # Get ECU data
        ecu_data = self.read_json(self.OBD_2_Output_Rx)

        # Check for param (json sub fields)
        if param:
            #--------------------------------------------------------------------------------------------------------------
            # Added this part for security access --> will return calculated key
            if param == "security_access":
                return self.get_sec_acc_calc_key(ecu_data=ecu_data)
            #--------------------------------------------------------------------------------------------------------------

            # Check if a param exists in the valid param list or if a sub-param is requested also
            if param not in self.valid_params and '.' not in param:  
                    return {"message": f"Param '{param}' not found in output json"}, 400
            
            # Check for sub-params (ex: 'engine_info.rpm')
            param_parts = param.split('.')

            if ecu_data and isinstance(ecu_data, list) and len(ecu_data) > 0:
                # json data is returned as a list and the info is the first element -> 0   
                data_to_return = ecu_data[0] 

                # Find the specified param is the JSON -> param.sub-param....
                try:
                    for part in param_parts:
                        data_to_return = data_to_return[part]  
                    return {f"{param}": data_to_return}, 200
                except KeyError:
                    return {"message": f"Param '{param}' not found in output json"}, 400
                
            # Return all ecu data if no param requested
            else:
                return {"message": "ECU data is empty or invalid."}, 400
        return ecu_data, 200
    
    ''' >>> PUT    '''#___PUT_METHOD___________________________________________________________
    def put(self) -> dict:
        """ 
            :Function name: put
            - Descr: Updates the ECU input data based on the provided JSON data in the request.
                     If the parameter is valid, it updates the respective field in the ECU input JSON.
                     For MongoDB snapshots:
                     - If snapshot_id and update_data are provided, it will update specific fields in the snapshot
                     Equivalent for PUT method.
                     Example request:PUT http://localhost:5000/ecu 
                                        {
                                            "security_access": {
                                                "auth_request": true,
                                                "key": 8978202516705421673549163187514582237}
                                        }
                                    -> updates the ECU input data with the provided JSON in the request body.
                     Example request:PUT http://localhost:5000/ecu?snapshot_id=20250504_2351
                                        {
                                            "update_data": {
                                                "coolant_temp": 95,
                                                "security_access.auth_request": true
                                            }
                                        }
                                    -> updates the specified fields in the MongoDB snapshot.
            :param: JSON body with the updated ECU input data or snapshot update data.
                    URL parameter 'snapshot_id' specifying the snapshot to update.
            :return: dict, rc.
            :response codes: 200 OK, 201 Created, 400 Bad Request, 401 Unauthorized, 404 Not Found, 406 Not Acceptable
        """
        # Validate API KEY return 401 if invalid
        validation_response = self.validate_api_key()
        if validation_response:
            return validation_response
        
        # Get data from the PUT request
        input_data = request.get_json()  
        if not input_data:
            return {"message": "Input data is empty or invalid."}, 406
        
        #*************************************************************************************
        # Handle MongoDB snapshot updates
        snapshot_id = request.args.get('snapshot_id')
        
        if snapshot_id:
            # Init connection to database
            self.mongo_db_handler = MongoDBHandler(uri=CONNECTION_STRING, db_name=DATABASE_NAME, collection_name=COLLECTION_NAME)
            
            # Get update_data from request
            update_data = input_data.get('update_data')
            if not update_data or not isinstance(update_data, dict):
                return {"message": "update_data is required and must be a dictionary."}, 400
            
            # Update snapshot in MongoDB
            success = self.mongo_db_handler.put_snapshot_in_db(snapshot_id, update_data)
            if success:
                return {"message": f"Snapshot '{snapshot_id}' updated successfully"}, 200
            else:
                return {"message": f"Failed to update snapshot '{snapshot_id}'"}, 404
        #*************************************************************************************
        
        # Read the current ECU input data from file
        ecu_input_data = self.read_json(self.OBD_2_Input_Tx)

        # If the ECU input data is empty or invalid, return an error
        if not ecu_input_data or not isinstance(ecu_input_data, dict):
            return {"message": "ECU input data is empty or invalid."}, 406
        
        #**********_UPDATE_DATA_************************************************************************************************************************************
        # Update the parameters in the ECU input dictionary; -> BULK UPDATE: change data if updates were made, else update with current data
        ecu_input_data.update({
            "error_injection": input_data.get("error_injection", ecu_input_data.get("error_injection")),
            "clear_error_memory": input_data.get("clear_error_memory", ecu_input_data.get("clear_error_memory")),
            "ign_stat": input_data.get("ign_stat", ecu_input_data.get("ign_stat")),
            "pedal_lvl": input_data.get("pedal_lvl", ecu_input_data.get("pedal_lvl")),
            "gear": input_data.get("gear", ecu_input_data.get("gear")),
            "manipulate_oil_levels": input_data.get("manipulate_oil_levels", ecu_input_data.get("manipulate_oil_levels")),
            "manipulate_coolant_levels": input_data.get("manipulate_coolant_levels", ecu_input_data.get("manipulate_coolant_levels")),
            "manipulate_voltage": input_data.get("manipulate_voltage", ecu_input_data.get("manipulate_voltage")),
            "security_access": {
                "auth_request": input_data.get("security_access", {}).get("auth_request", ecu_input_data.get("security_access", {}).get("auth_request")),
                "key": input_data.get("security_access", {}).get("key", ecu_input_data.get("security_access", {}).get("key")),
            }
        })
        #**********End_of_UPDATE_DATA_******************************************************************************************************************************
        
        # Save the updated data back to the JSON file
        self.write_json(self.OBD_2_Input_Tx, ecu_input_data)
        return {"message": "ECU input data updated successfully."}, 201
    
    ''' >>> POST   '''#___POST_METHOD__________________________________________________________
    def post(self) -> dict:
        """ 
            :Function name: post
            - Descr: Updates the ECU input data, specifically handling the 'error_injection' field.
                    * If 'error_injection' is provided in the request body, it updates the corresponding field in OBD_2_Input_Tx.
                    * Equivalnet with POST method.
                    * Test with: POST: "http://localhost:5000/ecu" and {"error_injection": ["EngErr_RpmSensorMalfunction", "EngErr_FuelConsmUnav"]}
            :param: JSON body with 'error_injection' field.
            :return: dict, rc.
            :response codes: 201 Created, 406 Not Acceptable, 401 Unauthorized
        """
        # Validate API KEY return 401 if invalid
        validation_response = self.validate_api_key()
        if validation_response:
            return validation_response

        # Get data from the POST request
        input_data = request.get_json()
        if not input_data:
            return {"message": "Input data is empty or invalid."}, 406

        # Read the current ECU input data from file
        ecu_input_data = self.read_json(self.OBD_2_Input_Tx)
        if not ecu_input_data or not isinstance(ecu_input_data, dict):
            return {"message": "ECU input data is empty or invalid."}, 406

        # Handle 'error_injection' separately
        if "error_injection" in input_data:
            ecu_input_data["error_injection"] = input_data["error_injection"]
            
        #*************************************************************************************
        # Handle "save_snapshot" --> post data to mongo db
        if "save_snapshot" in input_data and input_data["save_snapshot"] is True:
            
            # Init connection to database
            self.mongo_db_handler = MongoDBHandler(uri=CONNECTION_STRING, db_name=DATABASE_NAME, collection_name=COLLECTION_NAME)
            
            # Get ECU data
            ecu_data = self.read_json(self.OBD_2_Output_Rx)
            formatted_ecu_data_snapshot = db_con_utils.format_diag_snapshot(ecu_data)
            insertion_id = self.mongo_db_handler.post_snapshot_data_to_db(formatted_ecu_data_snapshot)
            if insertion_id:
                return {"message": "Snapshot saved to MongoDB.", "snapshot_id": str(insertion_id)}, 201
            else:
                return {"message": "Failed to save snapshot to MongoDB."}, 500
            
        # Save the updated data back to the JSON file
        self.write_json(self.OBD_2_Input_Tx, ecu_input_data)
        return {"message": "ECU input data updated successfully."}, 201
        
    ''' >>> DELETE '''#___DELETE_METHOD________________________________________________________
    def delete(self) -> dict:
        """
            :Function name: delete
            - Descr: Deletes a specific parameter or sub-field from the ECU output data based on the request.
                    If the parameter is 'clear_error_memory' or 'clear_error_log', it will toggle between True and False.
                    If the parameter is 'error_injection', it will delete the content of this subfield.
                    If the parameter targets a sub-field (e.g., 'error_log.ComErr_CanErr_Undervoltage'),
                    it will be removed from the ECU output data (`OBD_2_Output_Rx`).
                    For MongoDB snapshots:
                    - If snapshot_id is provided, it will delete the entire snapshot
                    - If snapshot_id and field_path are provided, it will delete a specific field from the snapshot
                    Equivalent to DELETE method
            :param: URL parameter 'param' specifying the field or sub-field to delete/set to False.
                    URL parameter 'snapshot_id' specifying the snapshot to delete or modify.
                    URL parameter 'field_path' specifying the field to delete from a snapshot.
            :return: dict, rc.
            :response codes: 200 OK, 400 Bad Request, 401 Unauthorized, 404 Not Found, 406 Not Acceptable, 500 Server Error
        """
        # Validate API KEY return 401 if invalid
        validation_response = self.validate_api_key()
        if validation_response:
            return validation_response

        #*************************************************************************************
        # Handle MongoDB snapshot deletions
        snapshot_id = request.args.get('snapshot_id')
        field_path = request.args.get('field_path')
        
        if snapshot_id:
            # Init connection to database
            self.mongo_db_handler = MongoDBHandler(uri=CONNECTION_STRING, db_name=DATABASE_NAME, collection_name=COLLECTION_NAME)
            
            if field_path:
                # Delete specific field from snapshot
                success = self.mongo_db_handler.delete_field_from_snapshot(snapshot_id, field_path)
                if success:
                    return {"message": f"Field '{field_path}' deleted from snapshot '{snapshot_id}' successfully"}, 200
                else:
                    return {"message": f"Failed to delete field '{field_path}' from snapshot '{snapshot_id}'"}, 404
            else:
                # Delete entire snapshot
                success = self.mongo_db_handler.delete_snapshot_from_db(snapshot_id)
                if success:
                    return {"message": f"Snapshot '{snapshot_id}' deleted successfully"}, 200
                else:
                    return {"message": f"Failed to delete snapshot '{snapshot_id}'"}, 404
        #*************************************************************************************

        # URL parameter; what do you want to delete from the ECU resource? 
        param = request.args.get('param', None)
        if not param: 
            return {"message": "Parameter 'param' is required in the request."}, 400

        #********** Handle OBD_2_Input_Tx operations **********
        '''
            Example requets:
            -> DELETE: http://localhost:5000/ecu?param=clear_error_memory
            -> DELETE: http://localhost:5000/ecu?param=clear_error_log
            -> DELETE: http://localhost:5000/ecu?param=error_injection
            -> DELETE: http://localhost:5000/ecu?param=parameter_to_delete
        '''
        if param in self.valid_delete_params:
            ecu_input_data = self.read_json(self.OBD_2_Input_Tx)
            if not ecu_input_data or not isinstance(ecu_input_data, dict):
                return {"message": "ECU input data is empty or invalid."}, 406
            #-----------------------------------------------------------------------------------------------
            # Clear the error injection list
            if param == "error_injection":
                ecu_input_data["error_injection"] = []
                        #-----------------------------------------------------------------------------------------------
            # Clear the error injection list
            if param == "parameter_to_delete":
                ecu_input_data["parameter_to_delete"] = ""
            #-----------------------------------------------------------------------------------------------
            # Toggle between True/False
            elif param == "clear_error_memory":
                ecu_input_data["clear_error_memory"] = not ecu_input_data.get("clear_error_memory", False) 
                #----------------------------------------------------------------------------------------------- 
            # Toggle between True/False
            elif param == "clear_error_log":
                ecu_input_data["clear_error_log"] = not ecu_input_data.get("clear_error_log", False)  
            #-----------------------------------------------------------------------------------------------
            # Save the updated data back to the JSON file
            self.write_json(self.OBD_2_Input_Tx, ecu_input_data)
            return {"message": f"ECU input data updated successfully. Modified: {param}"}, 200
        
        #********** Handle error_memory and error_log deletions in OBD_2_Input_Tx **********
        '''
            Example requets:
            -> DELETE: http://localhost:5000/ecu?param=error_log.EngErr_RpmSensorMalfunction
        '''
        if param.startswith("error_memory.") or param.startswith("error_log."):
            ecu_input_data = self.read_json(self.OBD_2_Input_Tx)
            ecu_input_data["parameter_to_delete"] = param  
            self.write_json(self.OBD_2_Input_Tx, ecu_input_data)
            return {"message": f"Set 'parameter_to_delete' to '{param}' in OBD_2_Input_Tx. ECU Sim will handle deletion."}, 200

        #********** Handle OBD_2_Output_Rx operations **********
        '''
            Example requets:
            -> DELETE: http://localhost:5000/ecu?param=engine_info.rpm
        '''
        ecu_output_data = self.read_json(self.OBD_2_Output_Rx)
        #-----------------------------------------------------------------------------------------------
        # Ensure the output data is a **list** and has at least one entry
        if not ecu_output_data or not isinstance(ecu_output_data, list) or len(ecu_output_data) == 0:
            return {"message": "ECU output data is empty or invalid."}, 406
        #-----------------------------------------------------------------------------------------------
        # Work on the first element (ecu_output_data[0])
        ecu_output_data = ecu_output_data[0]
        if "." in param:
            # Example: ["error_log", "ComErr_CanErr_Undervoltage"]
            keys = param.split(".")  
            current = ecu_output_data
            #-----------------------------------------------------------------------------------------------
            for key in keys[:-1]:  # Traverse to the second-last key
                if key in current and isinstance(current[key], dict):
                    current = current[key]
                else:
                    return {"message": f"Invalid path: {param}"}, 400
            #-----------------------------------------------------------------------------------------------
            # Remove the last key if it exists
            last_key = keys[-1]
            if last_key in current:
                del current[last_key]
            else:
                return {"message": f"Parameter '{param}' not found."}, 400
            #-----------------------------------------------------------------------------------------------
            # Save the updated output data **as a list** back to the JSON file
            self.write_json(self.OBD_2_Output_Rx, [ecu_output_data])  
            return {"message": f"ECU output data updated successfully. Deleted: {param}"}, 200

        return {"message": f"Invalid parameter: {param}"}, 400

  
# Add ecu resource to the API
diag_api.add_resource(Diag_API, "/ecu")


def start_api():
    """ To run the API in the main file"""
    mongo_db_handler = MongoDBHandler(uri=CONNECTION_STRING, db_name=DATABASE_NAME, collection_name=COLLECTION_NAME)
    mongo_db_handler.init_mongo_connection(uri= CONNECTION_STRING)
    diag_api_app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)

if __name__ == "__main__":
    diag_api_app.run(debug=True)
