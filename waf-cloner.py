import boto3
import json
import sys

def get_aws_profiles():
    session = boto3.Session()
    return session.available_profiles

def select_profile(profiles):
    print("Available AWS profiles:")
    for i, profile in enumerate(profiles, 1):
        print(f"{i}. {profile}")
    while True:
        try:
            choice = int(input("Select a profile number: "))
            if 1 <= choice <= len(profiles):
                return profiles[choice - 1]
            else:
                print("Invalid choice. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def select_region(prompt):
    regions = [
        ("1", "ap-south-1", "Mumbai (Regional)"),
        ("2", "us-east-1", "N. Virginia (Global)")
    ]
    print(f"\n{prompt}")
    for num, region, description in regions:
        print(f"{num}. {region} - {description}")
    while True:
        choice = input("Enter your choice (1 or 2): ")
        if choice in ["1", "2"]:
            return regions[int(choice) - 1][1]
        else:
            print("Invalid choice. Please enter 1 or 2.")

def get_web_acls(client, region):
    scope = 'REGIONAL' if region == 'ap-south-1' else 'CLOUDFRONT'
    response = client.list_web_acls(Scope=scope)
    return [(acl['Name'], acl['Id']) for acl in response['WebACLs']]

def select_web_acl(acls):
    print("\nAvailable Web ACLs:")
    for i, (name, _) in enumerate(acls, 1):
        print(f"{i}. {name}")
    while True:
        try:
            choice = int(input("Select a source Web ACL number: "))
            if 1 <= choice <= len(acls):
                return acls[choice - 1]
            else:
                print("Invalid choice. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number.")

import re

def sanitize_name(name):
    # Remove spaces and special characters, replace with underscores
    sanitized = re.sub(r'[^\w-]', '_', name)
    # Ensure the name starts with an alphanumeric character
    if not sanitized[0].isalnum():
        sanitized = 'a' + sanitized
    return sanitized

def clone_web_acl(source_client, target_client, source_acl, new_acl_name, new_description, source_region, target_region):
    source_acl_name, source_acl_id = source_acl
    source_scope = 'REGIONAL' if source_region == 'ap-south-1' else 'CLOUDFRONT'
    target_scope = 'REGIONAL' if target_region == 'ap-south-1' else 'CLOUDFRONT'
    
    # Get the source Web ACL
    response = source_client.get_web_acl(Name=source_acl_name, Id=source_acl_id, Scope=source_scope)
    web_acl = response['WebACL']

    # Sanitize the new ACL name
    new_acl_name = sanitize_name(new_acl_name)

    # Prepare the new Web ACL configuration
    new_web_acl = {
        'Name': new_acl_name,
        'Scope': target_scope,
        'DefaultAction': web_acl['DefaultAction'],
        'Description': new_description,
        'Rules': [],
        'VisibilityConfig': web_acl['VisibilityConfig']
    }

    # Process and clean up rules
    for rule in web_acl['Rules']:
        new_rule = rule.copy()
        
        # Check if the rule has a valid statement
        if 'Statement' not in new_rule or not new_rule['Statement']:
            print(f"Skipping rule '{new_rule.get('Name', 'Unnamed')}' due to missing or empty statement.")
            continue

        # Handle rules with region-specific resources
        if 'IPSetReferenceStatement' in new_rule.get('Statement', {}):
            if source_region != target_region:
                print(f"Skipping rule '{new_rule.get('Name', 'Unnamed')}' as it references a region-specific IP set and regions are different.")
                continue
            else:
                print(f"Keeping rule '{new_rule.get('Name', 'Unnamed')}' with IP set reference as source and target regions are the same.")

        # Remove RuleGroupReferenceStatement if present
        if 'RuleGroupReferenceStatement' in new_rule.get('Statement', {}):
            print(f"Skipping rule '{new_rule.get('Name', 'Unnamed')}' as it references a rule group.")
            continue
        
        # Remove CustomResponse if present
        if 'Action' in new_rule and 'Block' in new_rule['Action']:
            if 'CustomResponse' in new_rule['Action']['Block']:
                del new_rule['Action']['Block']['CustomResponse']
        
        # Add the cleaned rule to the new rules list
        new_web_acl['Rules'].append(new_rule)

    # Create the new Web ACL
    try:
        response = target_client.create_web_acl(**new_web_acl)
        print(f"\nSuccessfully cloned Web ACL. New ACL ID: {response['Summary']['Id']}")
        print(f"New ACL Name: {new_acl_name}")
    except target_client.exceptions.WAFInvalidParameterException as e:
        print(f"\nError: Invalid parameter when creating Web ACL.")
        print("Detailed error message:")
        print(json.dumps(e.response['Error'], indent=2))
        print("\nAttempting to create Web ACL without rules...")
        new_web_acl['Rules'] = []  # Remove all rules
        try:
            response = target_client.create_web_acl(**new_web_acl)
            print(f"\nSuccessfully created Web ACL without rules. New ACL ID: {response['Summary']['Id']}")
            print(f"New ACL Name: {new_acl_name}")
            print("Please add rules manually to this Web ACL.")
        except Exception as e2:
            print(f"\nFailed to create Web ACL without rules. Error: {str(e2)}")
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")
        print("Detailed error message:")
        print(json.dumps(e.response['Error'], indent=2))
        
def main():
    profiles = get_aws_profiles()
    selected_profile = select_profile(profiles)
    
    source_region = select_region("Select source region:")
    target_region = select_region("Select target region:")

    session = boto3.Session(profile_name=selected_profile)
    source_client = session.client('wafv2', region_name=source_region)
    target_client = session.client('wafv2', region_name=target_region)

    acls = get_web_acls(source_client, source_region)
    source_acl = select_web_acl(acls)

    new_acl_name = input("\nEnter a name for the new Web ACL: ")
    new_description = input("Enter a description for the new Web ACL: ")

    clone_web_acl(source_client, target_client, source_acl, new_acl_name, new_description, source_region, target_region)

if __name__ == "__main__":
    main()
