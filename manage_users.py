import argparse
import secrets
import sqlite3
import database

def create_user(first_name, last_name, role):
    # Construct User ID (First Initial + Last Name)
    user_id = f"{first_name[0].upper()}{last_name.capitalize()}"
    
    # Generate a secure invite token
    token = secrets.token_urlsafe(32)
    
    conn = database.get_db_connection()
    try:
        conn.execute(
            'INSERT INTO users (user_id, role, invite_token) VALUES (?, ?, ?)',
            (user_id, role, token)
        )
        conn.commit()
        print(f"\n✅ User successfully mapped to database.")
        print(f"------------------------------------------------")
        print(f"Name: {first_name} {last_name}")
        print(f"User ID: {user_id}")
        print(f"Role: {role.title()}")
        print(f"------------------------------------------------")
        print(f"Please copy the following invite link and send it to the user:")
        print(f"http://localhost:8000/set_password/{token}")
        print(f"------------------------------------------------\n")
    except sqlite3.IntegrityError:
        print(f"Error: User ID '{user_id}' already exists in the database.")
    finally:
        conn.close()

if __name__ == '__main__':
    database.init_db()
    parser = argparse.ArgumentParser(description="Manage UCSD Baseball Users")
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    create_parser = subparsers.add_parser('create', help="Create a new user invite")
    create_parser.add_argument('--first', required=True, help="User's first name")
    create_parser.add_argument('--last', required=True, help="User's last name")
    create_parser.add_argument('--role', required=True, choices=['player', 'coach', 'analyst'], help="User's role")
    
    args = parser.parse_args()
    
    if args.command == 'create':
        create_user(args.first, args.last, args.role)
