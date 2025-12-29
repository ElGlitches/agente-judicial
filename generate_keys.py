
import streamlit_authenticator as stauth

p1 = stauth.Hasher().hash('abc12345')
p2 = stauth.Hasher().hash('demo12345')
hashed_passwords = [p1, p2]
print("Hashes generated:")
print(f"Admin (abc12345): {hashed_passwords[0]}")
print(f"Demo (demo12345): {hashed_passwords[1]}")
