 #___GET_METHOD___________________________________________________________
    def get(self) -> dict:
        """ 
            :Function name: get
            - Descr: Returns JSON data for the ECU with a specific parameter or whole info
                     if no parameter is specified in the request.
                     Equivalent for GET method, ~ GET data by <id>; as the id are the params from the json file.
            - Example request with param: GET: http://localhost:5000/ecu?param=engine_info.rpm -> returns param "rpm" from
                               engine info sub-category of output json. 
            - Example request with param: GET: http://localhost:5000/ecu -> returns all info from json.
            :return: dict, rc
            :response codes: 200 OK, 400 Bad Request, 401 Unauthorized
        """
        # Validate API KEY return 401 if invalid
        validation_response = self.validate_api_key()
        if validation_response:
            return validation_response
        
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