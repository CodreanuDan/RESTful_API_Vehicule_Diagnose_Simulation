#***********************************************************************
# MODULE: key_generator
# SCOPE:  Auxilliary sub-module for diag_api, used for "key" calculation when a GET request for "seed" is sent from the api.
# REV: 1.0
#
# Created by: Codreanu Dan
# Descr:


#***********************************************************************

#***********************************************************************
class Key_Generator:
    """ """
    def __init__(self):
        """ """
        pass
    def KeyGen_genKey(self, seed: int) -> int:
        """ 
            :Function name: SecAcc_genKey
            - Descr: Generate key to complete the seed such that the sum of each pair of corresponding digits from the seed 
                    (excluding ECU_ID part) and the key is 10.
            :param seed: ECU_ID (12 digits) + 25 random digits
            :return: key: int
        """
        seed_str = str(seed)
        ecu_id = seed_str[:12]
        random_digits = seed_str[12:]
        key_str = ''.join(str(10 - int(digit)) for digit in random_digits)
        final_key = ecu_id + key_str  
        return int(final_key)  

    def KeyGen_checkKey(self, seed: int, key: int) -> bool:
        """ 
            :Function name: SecAcc_checkKey
            - Descr: Verifies if the provided key is valid by checking if the sum of each pair of corresponding digits 
                    from the seed (excluding ECU_ID part) and the key is 10.
            :param seed: ECU_ID (12 digits) + 25 random digits
            :param key: Key to be verified
            :return: True if the key is valid, False otherwise
        """
        seed_str, key_str = str(seed), str(key)
        if len(seed_str) != 37 or len(key_str) != 37:
            return False
        for s, k in zip(seed_str[-25:], key_str[-25:]):
            if int(s) + int(k) != 10:
                return False
        return True


if __name__ == "__main__":
    seed = 8978202516705689437561947923596528873 
    key_gen = Key_Generator()
    key = key_gen.KeyGen_genKey(seed=seed)
    print(f"*KEY:  {key}")
    print(f"*SEED: {seed}")
    is_valid = key_gen.KeyGen_checkKey(seed=seed, key=key)
    print(f"Key is valid: {is_valid}")  
