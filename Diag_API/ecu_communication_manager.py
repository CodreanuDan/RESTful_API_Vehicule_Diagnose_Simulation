#***********************************************************************
# MODULE: ecu_communication_manager
# SCOPE:  Auxilliary sub-module for diag_api, used for communication with TX and RX jsons.
# REV: 1.0
#
# Created by: Codreanu Dan
# Descr:


#***********************************************************************

#***********************************************************************
# IMPORTS:
import os
import json

class EcuCommunicationManger:
    """ """
    def __init__(self):
        """ 
            :return: Path to json files that simulate obd interface (Tx & Rx)
        """
        self.__VIRTUAL_ECU = 'VirtualCarECU'
        self.__OBD_2_PATH  = 'data'
        self.__OBD_2_TX    = 'OBD_2_INPUT.json'
        self.__OBD_2_RX    = 'OBD_2_OUTPUT.json'
        self.OBD_2_Input_Tx = os.path.join(os.path.dirname(os.path.dirname(__file__)),  self.__VIRTUAL_ECU, self.__OBD_2_PATH, self.__OBD_2_TX)
        self.OBD_2_Output_Rx = os.path.join(os.path.dirname(os.path.dirname(__file__)), self.__VIRTUAL_ECU, self.__OBD_2_PATH, self.__OBD_2_RX)

    def read_json(self, file_path:str) -> dict:
        """  
            :Function name: read_json
                - Descr:
            :param file_path: file_path 
            :return: dict
        """
        try:
            with open(file_path, "r") as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def write_json(self, file_path: str, data):
        """ 
            :Function name: write_json
                - Descr:
            :param file_path: file_path
            :param data: data to be written
            :return: None
        """
        with open(file_path, "w") as file:
            json.dump(data, file, indent=4)

if __name__ == "__main__":
    ecu_manager = EcuCommunicationManger()

    input_data = ecu_manager.read_json(ecu_manager.OBD_2_Input_Tx)
    output_data = ecu_manager.read_json(ecu_manager.OBD_2_Output_Rx)

    print("Input Data:", input_data)
    print("Output Data:", output_data)

