def check_pasword(password):
    """
    Check password if the number of characters is equal or more than 8.
    :param password: password
    :return: bool
    """
    if len(password) >= 8:
        return True
    else:
        return False
