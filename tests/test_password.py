from app.password import hash_password, verify_password


def test_password_hashing():
    result = hash_password("mysecretpassword")
    assert result != "mysecretpassword" 

def test_password_verification():
    hashed_password = hash_password("mysecretpassword")
    assert verify_password(hashed_password, "mysecretpassword") == True
    