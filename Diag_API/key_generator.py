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
            :param seed: ECU_ID (4 digits) + 15 random digits
            :return: key: int
        """
        seed_str = str(seed)
        ecu_id = seed_str[:4]
        random_digits = seed_str[4:]
        key_str = ''.join(str(10 - int(digit)) for digit in random_digits)
        final_key = ecu_id + key_str  
        return int(final_key)  

    def KeyGen_checkKey(self, seed: int, key: int) -> bool:
        """ 
            :Function name: SecAcc_checkKey
            - Descr: Verifies if the provided key is valid by checking if the sum of each pair of corresponding digits 
                    from the seed (excluding ECU_ID part) and the key is 10.
            :param seed: ECU_ID (4 digits) + 15 random digits
            :param key: Key to be verified
            :return: True if the key is valid, False otherwise
        """
        seed_str, key_str = str(seed), str(key)
        if len(seed_str) != 19 or len(key_str) != 19:
            return False
        for s, k in zip(seed_str[-15:], key_str[-15:]):
            if int(s) + int(k) != 10:
                return False
        return True


if __name__ == "__main__":
    seed = 1234567890123456789
    key_gen = Key_Generator()
    key = key_gen.KeyGen_genKey(seed=seed)
    print(f"*KEY:  {key}")
    print(f"*SEED: {seed}")
    is_valid = key_gen.KeyGen_checkKey(seed=seed, key=key)
    print(f"Key is valid: {is_valid}")  
