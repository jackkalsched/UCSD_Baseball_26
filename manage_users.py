import argparse
import base64
import json

def create_user(first_name, last_name, role):
    user_id = f"{first_name[0].upper()}{last_name.capitalize()}"
    
    payload = {
        "userId": user_id,
        "role": role
    }
    
    payload_str = json.dumps(payload)
    token = base64.b64encode(payload_str.encode('utf-8')).decode('utf-8')
    
    print(f"\n✅ User successfully mapped.")
    print(f"------------------------------------------------")
    print(f"Name: {first_name} {last_name}")
    print(f"User ID: {user_id}")
    print(f"Role: {role.title()}")
    print(f"------------------------------------------------")
    print(f"Please copy the following GitHub Pages invite link and send it to the user:")
    print(f"https://andrewzaletski.github.io/UCSD_Baseball_26/set_password.html?token={token}")
    print(f"(For local testing, use http://localhost:8000/set_password.html?token={token})")
    print(f"------------------------------------------------\n")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Manage UCSD Baseball Users (Static Builder)")
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    create_parser = subparsers.add_parser('create', help="Create a new user invite link")
    create_parser.add_argument('--first', required=True, help="User's first name")
    create_parser.add_argument('--last', required=True, help="User's last name")
    create_parser.add_argument('--role', required=True, choices=['player', 'coach', 'analyst'], help="User's role")
    
    args = parser.parse_args()
    
    if args.command == 'create':
        create_user(args.first, args.last, args.role)
