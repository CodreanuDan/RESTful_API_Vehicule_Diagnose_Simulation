from datetime import datetime
from typing import List, Dict 

class Diag_DataBaseCom_Utils:
    @staticmethod
    def format_diag_snapshot(payload: List | Dict, mechanic_comment: str = "") -> Dict:
        if isinstance(payload, List):
            if not payload:
                raise ValueError("Payload list is empty.")
            payload = payload[0]

        if not isinstance(payload, Dict):
            raise TypeError(f"Expected dict after list extraction, got {type(payload)}")

        # Extract timestamp and format it
        timestamp_str = payload.get("time_stamp")
        
        # Create a minute-based ID from timestamp
        minute_id = None
        if timestamp_str:
            try:
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                minute_id = f"DIAG_{timestamp.strftime('%Y%m%d_%H%M')}"
            except (ValueError, TypeError):
                # If timestamp format is invalid, use current time
                timestamp = datetime.now()
                minute_id = f"DIAG_{timestamp.strftime('%Y%m%d_%H%M')}"
        else:
            # If no timestamp provided, use current time
            timestamp = datetime.now()
            minute_id = f"DIAG_{timestamp.strftime('%Y%m%d_%H%M')}"

        diag_snapshot = {
            "report_id": minute_id,
            "time_stamp": timestamp_str or timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "error_log": payload.get("error_log", {}),
            "error_input": payload.get("error_input", []),
            "error_memory": payload.get("error_memory", {}),
            "ign_stat": payload.get("ign_stat"),
            "power_supply": payload.get("power_supply"),
            "coolant_temp": payload.get("engine_info", {}).get("coolant_temp"),
            "coolant_level": payload.get("engine_info", {}).get("coolant_level"),
            "oil_level": payload.get("engine_info", {}).get("oil_level"),
            "security_access": payload.get("security_access", {}),
            "mechanic_comment": mechanic_comment
        }

        # Create the key with the minute ID
        diag_key = f"DIAG_SNAPSHOT_{minute_id}"
        return {diag_key: diag_snapshot}