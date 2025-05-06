#***********************************************************************
# MODULE: main
# SCOPE:  Run threads for diag_api and virtual ECU.
# REV: 1.0
#
# Created by: Codreanu Dan
# Descr:


#***********************************************************************

#***********************************************************************
import threading as threading

from VirtualCarECU.car_simulation import VirtualECU
from Diag_API.diag_api import Diag_API, start_api
from Diag_API.key_generator import Key_Generator
from Diag_API.ecu_communication_manager import EcuCommunicationManger
from Diag_API.settings_manager import SettingsManager
from Diag_API.mongo_db_handler import MongoDBHandler

class Simulation(VirtualECU, Diag_API):
    """ """
    def __init__(self, file_path_out="VirtualCarECU/data/OBD_2_OUTPUT.json",
                       file_path_in="VirtualCarECU/data/OBD_2_INPUT.json"):
        """ """
        super().__init__(file_path_out, file_path_in)

    def __simulation_run_diag_api(self):
        """ 
            :Function name: __simulation_run_diag_api
            - Descr:    * runs the api in it`s own thread; stops with the program;
                        * pass the function as an refernce so the thread can run the function when is started.
        """
        self.diag_api_thread = threading.Thread(target=start_api,
                                                daemon=True)
        self.diag_api_thread.start()

    def __simulation_run_virtual_ecu(self):
        """ 
            :Function name: __simulation_run_virtual_ecu
            - Descr:    * runs the virtual in it`s own thread; stops with the program;
                        * pass the function as an refernce so the thread can run the function when is started.
        """
        self.virtual_ecu_thread = threading.Thread(target= self.VirtualECU_runSimulation,
                                                   daemon=True)
        self.virtual_ecu_thread.start()
        
    def simulation_main_function(self):
        """ 
            :Function name: simulation_main_function
            - Descr: * initialises the threads for virtual ecu and diag api.
        """
        self.__simulation_run_diag_api()
        self.__simulation_run_virtual_ecu()
        

if __name__ == "__main__":
    simulation = Simulation()
    simulation.simulation_main_function()

    # Block main execution to keep the threads alive
    while True:
        pass

