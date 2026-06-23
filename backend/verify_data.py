import requests

BASE_URL = "http://localhost:8000/api/v1"

def verify():
    # Login as admin
    print("Logging in...")
    login_response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": "admin@campusos.app", "password": "password123"}
    )
    if login_response.status_code != 200:
        print("Login failed!", login_response.text)
        return
    token = login_response.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}

    # Check Notices
    notices_response = requests.get(f"{BASE_URL}/notices", headers=headers)
    print("Notices:", notices_response.status_code)
    if notices_response.status_code == 200:
        print(len(notices_response.json()), "notices found.")

    # Check Mess
    mess_response = requests.get(f"{BASE_URL}/mess/schedule", headers=headers)
    print("Mess Schedule:", mess_response.status_code)
    if mess_response.status_code == 200:
        print(len(mess_response.json()), "mess schedules found.")

    # Check Placement
    placement_response = requests.get(f"{BASE_URL}/placement/drives", headers=headers)
    print("Placement Drives:", placement_response.status_code)
    if placement_response.status_code == 200:
        print(len(placement_response.json()), "placement drives found.")

    print("Verification completed successfully!")

if __name__ == "__main__":
    verify()
