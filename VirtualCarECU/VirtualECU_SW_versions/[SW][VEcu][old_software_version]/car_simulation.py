#***********************************************************************
# MODULE: car_simulation
# SCOPE:  Virtual simulation for a car ECU
# REV: 1.0
#
# Created by: Codreanu Dan
# Descr:


#***********************************************************************

#***********************************************************************
# IMPORTS:
import random
import time
from datetime import datetime
import json


class VirtualECU:
    """ """

    def __init__(self, file_path_out="VirtualCarECU/data/OBD_2_OUTPUT.json",   # TX_BUFFER
                         file_path_in="VirtualCarECU/data/OBD_2_INPUT.json"):  # RX_BUFFER
        """ """
        # _____SEETINGS__________________________________________________________
        # ***********************************************************************
        self.ON  = True
        self.OFF = False
        self.DEBUG = self.ON
        # self.DEBUG = self.OFF
        # _____CAR_DATA__________________________________________________________
        # ***********************************************************************
        self.ECU_ID = 8978 # Generic ID 4digits
        # ***********************************************************************
        self.gear_ratio = \
            {
                "N": 1.0,
                "1": 3.1,
                "2": 1.912,
                "3": 1.288,
                "4": 0.949,
                "5": 0.998,
                "6": 0.958,
                "R": 3.287
            }
        # -----------------------------------------------------------------------
        self.power_curve = \
            {
                "IDLE":    [800,   50],   # rpm, hp
                "LOW":     [2000,  80],
                "MID":     [3000, 120],
                "PEAK":    [4000, 150],   # rpm, hp (Max Power)
                "HIGH":    [4500, 135],
                "REDLINE": [5000, 125],
            }
        # _____CAN_BUS___________________________________________________________
        # ***********************************************************************
        self.file_path_out = file_path_out  # TX_BUFFER
        self.file_path_in = file_path_in   # RX_BUFFER
        # _____CAN_COM_DATA_&_SIGNALS____________________________________________
        # ***********************************************************************
        self.error_dict = \
            {
                0xE0110:  "EngErr_RpmSensorMalfunction",
                0xE0111:  "EngErr_FuelConsmUnav",
                0xE0112:  "EngErr_SpdmtrFault",
                0xE0120:  "EngErr_EngCoolOverheat",
                0xE0121:  "EngErr_OilLvlLow",
                0xE0122:  "EngErr_CoolLvlLow",
                0xE0130:  "EngErr_IgnMalfunction",
                0xE0210:  "ComErr_CanErr_LossOfComm",
                0xE0211:  "ComErr_CanErr_Overvoltage",
                0xE0212:  "ComErr_CanErr_Undervoltage",
                0xE0310:  "ElErr_Overvoltage",
                0xE0311:  "ElErr_Undervoltage",
            }
        # -----Error-Memory
        self.error_input = []       #  in error input if the error is present will set the status to active in err mem and set the error in err log
        self.error_memory = {}      #  error and error status: active or passive
        self.error_log = {}         #  error and timestamp when the error was triggerd |error_log = a resource created just for POST method
        # -----------------------------------------------------------------------
        # -----Signals
        self.signals = \
            {
                "ign_stat": {
                    0: "0_OFF",
                    1: "1_IGN",
                    2: "2_ACC",
                    3: "3_ERR",
                },
                "can_com": {
                    0: "Security_Access_LOCKED",
                    1: "Security_Access_UNLOCKED",
                    2: "Security_Access_DENIED",
                }
            }
        # -----------------------------------------------------------------------
        # -----Ignition-Status
        self.act_ign_stat = 0
        # -----------------------------------------------------------------------
        # -----Security_Access
        self.SECURITY_ACCESS_LOCKED = 0
        self.SECURITY_ACCESS_UNLOCKED = 1
        self.SECURITY_ACCESS_DENIED = 2
        if self.DEBUG == self.ON:
            self.security_access = 1
        elif self.DEBUG == self.OFF:
            self.security_access = 0
        self.NULL = None
        self.seed = self.NULL
        self.key = 0
        # ***********************************************************************

    
    # *>>_____ERROR_MNGMT____________________________________________________
    # ***********************************************************************
    def ErrMng_addErrorToMemory(self, error_code: int, error_input: list):
        """  """
        # a flag that signals that error_memory and error_log can be manipulated by the diag api
        if self.can_handle_err_mng_flag == False: # if set to True we can delete the entries
            if error_code not in self.error_memory and error_code in error_input:
                self.error_memory[error_code] = "active"
            if error_code not in self.error_log and error_input != []:
                self.error_log[error_code] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            else:
                pass
        else:
            pass
    #------------------------------------------------------------------------
    def ErrMng_checkActiveError(self, error_input: list):
        """ """
        for error in self.error_memory.keys():
            # a flag that signals that error_memory and error_log can be manipulated by the diag api
            if self.can_handle_err_mng_flag == False: # if set to True we can delete the entries
                if error in error_input and self.error_memory[error] == "passive":
                    self.error_memory[error] = "active"
                elif error not in error_input:
                    self.error_memory[error] = "passive"
            else:
                pass
    # -----------------------------------------------------------------------
    def ErrMng_clearErrorMemory(self, clear_flag: bool):
        """ """
        try:
            # Handle a single element from the list --> DELETE methods 
            if "error_memory." in self.parameter_to_delete:
                __param = self.parameter_to_delete.removeprefix("error_memory.")
                if __param in self.error_memory:
                    self.error_memory.pop(__param)
             # Handle all elements from the list --> DELETE methods
            if clear_flag == True:
                self.error_memory.clear()
        except Exception as e:
            print(f"ErrMng_clearErrorMemory:Error occurred: {e}")
    # -----------------------------------------------------------------------
    def ErrMng_clearErrorLog(self, clear_flag: bool):
        """ """
        try:
            # Handle a single element from the list --> DELETE methods
            if "error_log." in self.parameter_to_delete:
                __param = self.parameter_to_delete.removeprefix("error_log.")
                if __param in self.error_log:
                    self.error_log.pop(__param)
            # Handle all elements from the list --> DELETE methods
            if clear_flag == True:
                self.error_log.clear()
        except Exception as e:
            print(f"ErrMng_clearErrorLog:Error occurred: {e}")
    # -----------------------------------------------------------------------
    def ErrMng_errInjRemoveDupl(self, error_input: list):
        """  """
        seen = set()
        error_input[:] = [err for err in error_input if not (
            err in seen or seen.add(err))]
    # _____end_of_ERROR_MNGMT_____________________________________________<<*
    # ***********************************************************************


    # *>>_____SECURITY_ACCESS________________________________________________
    # ***********************************************************************
    def SecAcc_mainFunction(self, auth_req: bool):
        if auth_req == True: 
            if self.seed == self.NULL:
                self.seed = self.SecAcc_genSeed()
            if self.key != 0 and self.seed != 0:
                self.auth_response = self.SecAcc_checkKey(seed=self.seed, key=self.key)
                if self.auth_response == True:
                        self.security_access = self.SECURITY_ACCESS_UNLOCKED
                        self.seed = 0
                elif self.auth_response == False:
                    self.security_access = self.SECURITY_ACCESS_DENIED
        elif auth_req == False and self.key != 0 and self.DEBUG == self.OFF:
            self.security_access = self.SECURITY_ACCESS_DENIED
        elif auth_req == False and self.key == 0 and self.DEBUG == self.OFF:
            self.security_access = self.SECURITY_ACCESS_LOCKED
    # -----------------------------------------------------------------------
    def SecAcc_genSeed(self) -> int:
        """ 
            :Function name: SecAcc_genSeed
            - Descr: Generate seed for security access unlock:
                     ECU_ID(4 digits) + 15 random number seed 
            :return: seed:int
        """
        self.__seed = str(self.ECU_ID) + \
            ''.join(str(random.randint(1, 9)) for _ in range(15))
        return int(self.__seed)
    # -----------------------------------------------------------------------
    def SecAcc_checkKey(self, seed: int, key: int) -> bool:
        """ 
            :Function name: SecAcc_checkKey
            - Descr: Verifies if the provided key is valid by checking if the sum of each pair of corresponding digits 
                    from the seed (excluding ECU_ID part) and the key is 10.
            :param seed: ECU_ID (4 digits) + 15 random digits
            :param key: Key to be verified
            :return: True if the key is valid, False otherwise
        """
        seed_digits = str(seed)[-15:]
        key_digits = str(key)[-15:]
        if len(key_digits) != 15:
            return False
        for s, k in zip(seed_digits, key_digits):
            if int(s) + int(k) != 10:
                return False
        return True
    # _____end_of_SECURITY_ACCESS_________________________________________<<*
    # ***********************************************************************


    # *>>_____ENGINE_MNGMT___________________________________________________
    # ***********************************************************************
    def EngStat_MainFunction(self, gear: str, pedal_lvl: int, error_input: list, ign_stat: int) -> list:
        """ """
        self.engine_status_data = []
        # ___Check_IGN_STAT___________________________________________________________
        # ****************************************************************************
        self.act_ign_stat = ign_stat
        if self.error_dict[0xE0311] in self.error_memory and self.error_memory[self.error_dict[0xE0311]] == "active":
            # -----Manage-Error--------------------------------------------------
            if self.error_dict[0xE0130] not in error_input:
                self.error_input.append(self.error_dict[0xE0130])
            self.ErrMng_addErrorToMemory(
                error_code=self.error_dict[0xE0130], error_input=self.error_input)
            # -------------------------------------------------------------------
            if self.error_dict[0xE0130] in self.error_memory and self.error_memory[self.error_dict[0xE0130]] == "active":
                # -----Manage-Error--------------------------------------------------
                self.act_ign_stat = 0
                # -------------------------------------------------------------------
        # ___Check_Engine_Status______________________________________________________
        # ****************************************************************************
        self.real_rpm = self.EngStat_CalcRpm(gear=gear, pedal_lvl=pedal_lvl, ign_stat=self.act_ign_stat, error_memory=["EMPTY"])
         # ****************************************************************************
        # -----Error-Response
        if self.act_ign_stat == 0 or self.act_ign_stat == 3 or self.error_dict[0xE0110] in error_input:
            # -----Manage-Error--------------------------------------------------
            if self.error_dict[0xE0130] in error_input:
                self.error_input.append(self.error_dict[0xE0130])
                self.ErrMng_addErrorToMemory(error_code=self.error_dict[0xE0130], error_input=self.error_input)  # IGN_ERR
            self.ErrMng_addErrorToMemory(error_code=self.error_dict[0xE0110], error_input=self.error_input)  # RPM_ERR
        if (self.error_dict[0xE0110] in self.error_memory and self.error_memory[self.error_dict[0xE0110]] == "active") or self.act_ign_stat == 0:
            # -----Manage-Error--------------------------------------------------
            if self.error_dict[0xE0111] not in error_input and self.act_ign_stat != 0:
                self.error_input.append(self.error_dict[0xE0111])
            self.ErrMng_addErrorToMemory(error_code=self.error_dict[0xE0111], error_input=self.error_input)  # INST_FUEL_CONSM_ERR
            # --------------------------------------------------------------------
            self.rpm = 0
            self.engine_status_data.append(self.rpm)
            self.power = 0
            self.engine_status_data.append(self.power)
            self.torque = 0
            self.engine_status_data.append(self.torque)
        # -----Normal-Case
        else:
            self.rpm = self.EngStat_CalcRpm(gear=gear, pedal_lvl=pedal_lvl, ign_stat=self.act_ign_stat, error_memory=error_input)
            self.engine_status_data.append(self.rpm)
            self.power = self.EngStat_calcPwr(rpm=self.rpm)
            self.engine_status_data.append(self.power)
            self.torque = self.EngStat_calcTorque(rpm=self.rpm, power=self.power, pedal_lvl=pedal_lvl)
            self.engine_status_data.append(self.torque)
        # ___Check_Engine_Sensors_____________________________________________________
        # ****************************************************************************
        # -----Normal-Case
        fluid_level = self.EngStat_fluidSensors(
            rpm=self.rpm, ign_stat=self.act_ign_stat)
        self.__manipulate_coolant_levels = self.manipulate_coolant_levels
        self.coolant_level = fluid_level[0] + self.__manipulate_coolant_levels
        self.__manipulate_oil_levels = self.manipulate_oil_levels
        self.oil_level = fluid_level[1] + self.__manipulate_oil_levels
        self.fuel_consumption = self.EngStat_calcFuelCons(rpm=self.rpm)
        self.coolant_temp = self.EngStat_coolTemp(rpm=self.real_rpm)
        self.engine_status_data.append(self.coolant_temp)
        # -----Error-Response
        VALID_SIG = [0, 1, 2]
        RPM_THRESHOLD = 825
        MIN_LEVEL_RUN = 95
        MIN_LEVEL_IDLE = 70
        if self.act_ign_stat in VALID_SIG and self.rpm > RPM_THRESHOLD and self.coolant_level < MIN_LEVEL_RUN:
            # -----Manage-Error--------------------------------------------------
            self.error_input.append(self.error_dict[0xE0122])
            self.ErrMng_addErrorToMemory(
                error_code=self.error_dict[0xE0122], error_input=self.error_input)
        if self.act_ign_stat in VALID_SIG and self.rpm < RPM_THRESHOLD:
            if self.coolant_level < MIN_LEVEL_IDLE:
                # -----Manage-Error--------------------------------------------------
                self.error_input.append(self.error_dict[0xE0122])
                self.ErrMng_addErrorToMemory(error_code=self.error_dict[0xE0122], error_input=self.error_input)
        if self.act_ign_stat in VALID_SIG and self.rpm > RPM_THRESHOLD and self.oil_level < MIN_LEVEL_RUN:
            # -----Manage-Error--------------------------------------------------
            self.error_input.append(self.error_dict[0xE0121])
            self.ErrMng_addErrorToMemory(error_code=self.error_dict[0xE0121], error_input=self.error_input)
        if self.act_ign_stat in VALID_SIG and self.rpm < RPM_THRESHOLD:
            if self.oil_level < MIN_LEVEL_IDLE:
                # -----Manage-Error--------------------------------------------------
                self.error_input.append(self.error_dict[0xE0121])
                self.ErrMng_addErrorToMemory(error_code=self.error_dict[0xE0121], error_input=self.error_input)
        # ___Calc_Speed_______________________________________________________________
        # ****************************************************************************
        self.speed = self.EngStat_calcSpeed(rpm=self.rpm, gear=self.gear)
        # ****************************************************************************
        return self.engine_status_data
    # -----------------------------------------------------------------------
    def EngStat_CalcRpm(self, gear: str, pedal_lvl: int, ign_stat: int, error_memory: list) -> int:
        """ """
        MAX_RPM = 5000
        gear_ratio = self.gear_ratio[gear]
        if pedal_lvl == 0:
            rpm = random.randint(790, 810)
        elif self.error_dict[0xE0110] in error_memory or ign_stat == 0:
            rpm = 0
        elif pedal_lvl > 0:
            K = 42
            TOLERANCE = 0.01
            rpm = int((gear_ratio * pedal_lvl) * K + 800)
            rpm = random.randint(int(rpm - (rpm * TOLERANCE)),
                                 int(rpm + (rpm * TOLERANCE)))
            self.act_ign_stat = 2
        return rpm if rpm <= MAX_RPM else MAX_RPM
    # -----------------------------------------------------------------------
    def EngStat_calcPwr(self, rpm: int) -> int:
        """ """
        rpm_points = [v[0] for v in self.power_curve.values()]
        power_points = [v[1] for v in self.power_curve.values()]

        if rpm <= rpm_points[0]:
            return power_points[0]
        elif rpm >= rpm_points[-1]:
            return power_points[-1]

        for i in range(len(rpm_points) - 1):
            if rpm_points[i] <= rpm < rpm_points[i + 1]:
                TOLERANCE = 0.02
                power = int(self.EngStat_getPwrCurve(
                    rpm, rpm_points[i], rpm_points[i + 1], power_points[i], power_points[i + 1]))
                power = random.randint(
                    int(power - (power * TOLERANCE)), int(power + (power * TOLERANCE)))
                return power
        return power_points[-1]  # Default fail-safe
    # -----------------------------------------------------------------------
    def EngStat_getPwrCurve(self, x: int, x1: int, x2: int, y1: int, y2: int) -> float:
        """ """
        return y1 + (x - x1) * (y2 - y1) / (x2 - x1)
    # -----------------------------------------------------------------------
    def EngStat_calcTorque(self, rpm: int, power: int, pedal_lvl: int) -> int:
        """ """
        TORQUE_FACTOR = 9549
        RAL_TOL = 0.1
        RPM_IDLE = 800
        ACTUAL_RALANTI = RPM_IDLE + RAL_TOL * RPM_IDLE

        if rpm >= ACTUAL_RALANTI:
            torque = (power * TORQUE_FACTOR) / rpm
        elif rpm <= ACTUAL_RALANTI:
            torque = (power * TORQUE_FACTOR) / rpm - 300

        if pedal_lvl < 26:
            torque -= 200
        if pedal_lvl <= 12:
            torque = random.randint(156, 166)

        return int(torque)
    # -----------------------------------------------------------------------
    def EngStat_fluidSensors(self, rpm: int, ign_stat: int) -> list[int]:
        VALID_SIG = [1, 2]
        RPM_THRESHOLD = 825
        MIN_LEVEL = 95
        __coolant_level = random.randint(79, 81)
        __oil_level = random.randint(79, 81)
        # ___Handle_Cooling_Liquid_Level______________________________________________
        # ****************************************************************************
        if ign_stat not in VALID_SIG or rpm < RPM_THRESHOLD:
            pass
        elif ign_stat in VALID_SIG and rpm > RPM_THRESHOLD:
            __coolant_level = random.randint(118, 122)
        # ___Handle_Oil_Level_________________________________________________________
        # ****************************************************************************
        if ign_stat not in VALID_SIG or rpm < RPM_THRESHOLD:
            pass
        elif ign_stat in VALID_SIG and rpm > RPM_THRESHOLD:
            __oil_level = random.randint(118, 122)
        # ****************************************************************************
        return [__coolant_level, __oil_level]
    # -----------------------------------------------------------------------
    def EngStat_calcFuelCons(self, rpm: int) -> float:
        """   """
        if self.act_ign_stat == 0:
            return 0.0
        elif self.error_dict[0xE0111] in self.error_memory and self.error_memory[self.error_dict[0xE0111]] == "active": # "EngErr_FuelConsmUnav"
            return 0.0
        else:
            IDLE_RPM = 800
            MAX_RPM = 6000
            IDLE_CONS = 0.8
            MAX_CONS = 15

            a = (MAX_CONS - IDLE_CONS) / (MAX_RPM - IDLE_RPM)
            b = IDLE_CONS - a * IDLE_RPM

            fuel_consumption = a * rpm + b
            return round(fuel_consumption, 2)
    # -----------------------------------------------------------------------
    def EngStat_coolTemp(self, rpm: int) -> int:
        self.__temp = random.randint(87, 92)
        IGN_VALID_STATES = [0]
        UNDER_REDLINE = 4300
        OVERHEAT_NO_LIQUIDS_RPM = 2500
        OVERHEAT_TEMP = 130
        if self.act_ign_stat not in IGN_VALID_STATES and rpm > UNDER_REDLINE:
            self.__temp = random.randint(97, 102)
        if self.act_ign_stat not in IGN_VALID_STATES and rpm > OVERHEAT_NO_LIQUIDS_RPM:
            if ((self.error_dict[0xE0122] in self.error_memory and self.error_memory[self.error_dict[0xE0122]] == "active")
                    or (self.error_dict[0xE0121] in self.error_memory and self.error_memory[self.error_dict[0xE0121]] == "active")):   
                self.__temp = random.randint(132, 137)
                if self.__temp > OVERHEAT_TEMP:
                    if self.error_dict[0xE0120] not in self.error_input:
                        self.error_input.append(self.error_dict[0xE0120])
                    self.ErrMng_addErrorToMemory(
                        error_code=self.error_dict[0xE0120], error_input=self.error_input)  # OVERHEAT_ERROR
                if ((self.error_dict[0xE0122] in self.error_memory and self.error_memory[self.error_dict[0xE0122]] == "passive")
                        or (self.error_dict[0xE0121] in self.error_memory and self.error_memory[self.error_dict[0xE0121]] == "passive")):
                    self.error_input.remove(self.error_dict[0xE0120])
                    if self.act_ign_stat not in IGN_VALID_STATES and rpm > OVERHEAT_NO_LIQUIDS_RPM:
                        self.__temp = random.randint(97, 102)
                    else:
                        self.__temp = random.randint(87, 92)
        return self.__temp
    # -----------------------------------------------------------------------
    def EngStat_calcSpeed(self, rpm: int, gear: str) -> int:
        """  """
        if self.error_dict[0xE0112] in self.error_input:
                self.ErrMng_addErrorToMemory(error_code=self.error_dict[0xE0112], error_input=self.error_input)
        if rpm != 0 or self.error_dict[0xE0112] not in self.error_input:
            if rpm == 0 or gear not in self.gear_ratio:
                return 0
            if gear == "N":
                return 0
            WHEEL_RADIUS_INCH = 16 #inch
            ONE_INCH = 2.54
            WHEEL_RADIUS_CM = WHEEL_RADIUS_INCH * ONE_INCH
            FINAL_DRIVE_RATIO = 3.9  # Raport  diferential
            PI = 3.1416
            gear_ratio = self.gear_ratio[gear]
            if gear_ratio == 0:
                return 0.0  
            speed_mps = (rpm * WHEEL_RADIUS_CM * 2 * PI) / (gear_ratio * FINAL_DRIVE_RATIO * 6000)
            speed_kmh = speed_mps * 3.6
            return int(speed_kmh) if self.error_dict[0xE0112] not in self.error_input else 0
    # _____end_of_ENGINE_MNGMT____________________________________________<<*
    # ***********************************************************************


    # *>>_____POWER_SRC______________________________________________________
    # ***********************************************************************
    def PwSup_MainFunction(self):
        """ """
        self.__manipulate_voltage = self.manipulate_voltage
        # -----Normal-Case
        if (self.error_dict[0xE0310] not in self.error_input
                and self.error_dict[0xE0311] not in self.error_input):
            if self.act_ign_stat == 0:    # OFF
                self.voltage = round(random.uniform(
                    11.9, 12.1), 2) + self.__manipulate_voltage
            elif self.act_ign_stat == 1:  # IGN
                self.voltage = round(random.uniform(
                    12.9, 13.1), 2) + self.__manipulate_voltage
            elif self.act_ign_stat == 2:  # ACC
                self.voltage = round(random.uniform(
                    13.9, 14.1), 2) + self.__manipulate_voltage
        # -----Voltage-Error-Injection
        UNDERVOLTAGE_THRESHOLD = 7.5
        OVERVOLATGE_THRESHOLD = 17.4
        CAN_OVERVOLTAGE = 19.0
        CAN_UNDERVOLTAGE = 5.0
        # -----Engine-Errors
        if self.voltage < UNDERVOLTAGE_THRESHOLD:
            # -----Manage-Error--------------------------------------------------
            self.error_input.append(self.error_dict[0xE0311])
            self.ErrMng_addErrorToMemory(
                error_code=self.error_dict[0xE0311], error_input=self.error_input)
            # --------------------------------------------------------------------
        if self.voltage > OVERVOLATGE_THRESHOLD:
            # -----Manage-Error--------------------------------------------------
            self.error_input.append(self.error_dict[0xE0310])
            self.ErrMng_addErrorToMemory(
                error_code=self.error_dict[0xE0310], error_input=self.error_input)
            # --------------------------------------------------------------------
        # -----CAN-Errors
        if self.voltage > CAN_OVERVOLTAGE:
            # -----Manage-Error--------------------------------------------------
            self.error_input.append(self.error_dict[0xE0211])
            self.ErrMng_addErrorToMemory(
                error_code=self.error_dict[0xE0211], error_input=self.error_input)
            # --------------------------------------------------------------------
        if self.voltage < CAN_UNDERVOLTAGE:
            # -----Manage-Error--------------------------------------------------
            self.error_input.append(self.error_dict[0xE0212])
            self.ErrMng_addErrorToMemory(
                error_code=self.error_dict[0xE0212], error_input=self.error_input)
            # --------------------------------------------------------------------
    # _____end_of_POWER_SRC_______________________________________________<<*
    # ***********************************************************************


    # *>>_____CAN_COM________________________________________________________
    # ***********************************************************************
    def CanCom_RX(self):
        """ """
        try:
            with open(self.file_path_in, "r") as f:
                #-------------------------------------------------------------------------------------------------------------------
                inputs = json.load(f)
                #-------------------------------------------------------------------------------------------------------------------
                self.gear = inputs.get("gear", "N")
                self.pedal_lvl = inputs.get("pedal_lvl", 0)
                self.ign_stat = inputs.get("ign_stat", 1)
                self.error_input = inputs.get("error_injection", [])
                self.manipulate_oil_levels = inputs.get("manipulate_oil_levels", 0)
                self.manipulate_coolant_levels = inputs.get("manipulate_coolant_levels", 0)
                self.manipulate_voltage = inputs.get("manipulate_voltage", 0)
                self.clear_error_memory = inputs.get("clear_error_memory", False)
                self.clear_error_log = inputs.get("clear_error_log", False)
                # this param (str) is used for DELETE method 
                self.parameter_to_delete = inputs.get("parameter_to_delete", "")
                # a flag that signals that error_memory and error_log can be manipulated by the diag api
                self.can_handle_err_mng_flag = inputs.get("can_handle_error_manager", False)
                self.gear = inputs.get("gear", 'N')
                self.auth_request = inputs.get("security_access", {}).get("auth_request", True)
                self.key = inputs.get("security_access", {}).get("key", 0)
                #-------------------------------------------------------------------------------------------------------------------
        except FileNotFoundError:
            print(f"::RX_COM:: {self.file_path_in} :: Error ::")
    # -----------------------------------------------------------------------
    def CanCom_TX(self):
        """ """
        self.__comm_error = False
        # ______MANAGE_BUS_ERRORS______________________________________________________________________
        # *********************************************************************************************
        if (self.error_dict[0xE0210] in self.error_input
            or self.error_dict[0xE0211] in self.error_input
                or self.error_dict[0xE0212] in self.error_input):
            if self.error_dict[0xE0210] in self.error_input:
                # -----Manage-Error--------------------------------------------------
                if self.error_dict[0xE0210] not in self.error_input:
                    self.error_input.append(self.error_dict[0xE0210])
                self.ErrMng_addErrorToMemory(
                    error_code=self.error_dict[0xE0210], error_input=self.error_input)
            self.__comm_error = True
        # ______MANAGE_BUS_TX__________________________________________________________________________
        # *********************************************************************************************
        if (self.error_dict[0xE0210] not in self.error_input
            or self.error_dict[0xE0211] not in self.error_input
                or self.error_dict[0xE0212] not in self.error_input):
            if self.security_access == self.SECURITY_ACCESS_UNLOCKED:
                car_status = {
                    "ign_stat": self.signals["ign_stat"][self.act_ign_stat],
                    "power_supply": self.voltage,
                    "engine_info": {
                        "rpm": self.rpm,
                        "speed": self.speed,
                        "gear": self.gear,
                        "power": self.power,
                        "torque": self.torque,
                        "fuel_consumtion": self.fuel_consumption,
                        "coolant_temp": self.coolant_temp,
                        "coolant_level": self.coolant_level,
                        "oil_level": self.oil_level,
                        "pedal_lvl": self.pedal_lvl,
                    },
                    "error_log": self.error_log,
                    "error_input": self.error_input,
                    "error_memory": self.error_memory,
                    "can_handle_error_manager": self.can_handle_err_mng_flag,
                    "clear_error_memory": self.clear_error_memory,
                    "clear_error_log": self.clear_error_log,
                    "security_access":
                    {
                        "auth_response": [self.security_access, self.signals["can_com"].get(self.security_access, "Unknown")],
                        "auth_request": self.auth_request,
                        "seed": self.seed,
                        "key": self.key,
                    },
                    "time_stamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "REAL_RPM": self.real_rpm,
                }
            elif (self.security_access == self.SECURITY_ACCESS_LOCKED 
                or self.security_access == self.SECURITY_ACCESS_DENIED):
                car_status = {
                    "ign_stat": "401",
                    "power_supply": 401,
                    "engine_info":
                    {
                        "rpm": 401,
                        "speed": 401,
                        "gear": "401",
                        "power": 401,
                        "torque": 401,
                        "fuel_consumtion": 401,
                        "coolant_temp": 401,
                        "coolant_level": 401,
                        "oil_level": 401,
                        "pedal_lvl": 401,
                    },
                    "error_log": {},
                    "error_input": [],
                    "error_memory": {},
                    "can_handle_error_manager": self.can_handle_err_mng_flag,
                    "clear_error_memory": self.clear_error_memory,
                    "clear_error_log": self.clear_error_log,
                    "security_access":
                    {
                        "auth_response": [self.security_access, self.signals["can_com"].get(self.security_access, "Unknown")],
                        "auth_request": self.auth_request,
                        "seed": self.seed,
                        "key": self.key,
                    },
                    "time_stamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "REAL_RPM": 401,
                }
        # ______SEND_DATA_TO_CAN_BUS___________________________________________________________________
        # *********************************************************************************************
        # -----Simulate-CanError
        if self.__comm_error == True:
            pass
        try:
            with open(self.file_path_out, "r") as f:
                existing_data = json.load(f)
                if len(existing_data) > 0:
                    existing_data[-1] = car_status
                else:
                    existing_data.append(car_status)
        except (FileNotFoundError, json.JSONDecodeError):
            existing_data = [car_status]
        try:
            with open(self.file_path_out, "w") as f:
                json.dump(existing_data, f, indent=4)
        except FileNotFoundError:
            print(f"File {self.file_path_out} not found!")
        # *********************************************************************************************
    # _____end_of_CAN_COM_________________________________________________<<*
    # ***********************************************************************


    # *>>_____SIMULATION______________________________________________________
    # ***********************************************************************
    def VirtualECU_runSimulation(self):
        """ """
        while True:
            self.CanCom_RX()
            self.SecAcc_mainFunction(auth_req=self.auth_request)
            self.PwSup_MainFunction()
            self.EngStat_MainFunction(gear=self.gear, pedal_lvl=self.pedal_lvl,
                                      error_input=self.error_input, ign_stat=self.ign_stat)
            self.CanCom_TX()
            self.ErrMng_checkActiveError(error_input=self.error_input)
            self.ErrMng_clearErrorMemory(clear_flag=self.clear_error_memory)
            self.ErrMng_clearErrorLog(clear_flag=self.clear_error_log)
            self.ErrMng_errInjRemoveDupl(error_input=self.error_input)
            time.sleep(1)
    # _____end_of_SIMULATION______________________________________________<<*
    # ***********************************************************************


if __name__ == "__main__":
    car_sim = VirtualECU()
    car_sim.VirtualECU_runSimulation()
