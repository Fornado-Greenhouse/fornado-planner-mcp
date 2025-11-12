#!/usr/bin/env python3

import json


def main():
    print("=" * 80)
    print("Microsoft Planner MCP Server - Azure App Registration Guide")
    print("=" * 80)
    print()
    
    required_permissions = {
        "Microsoft Graph API Permissions": [
            "Tasks.ReadWrite (Delegated)",
            "Tasks.ReadWrite.Shared (Delegated)",
            "Group.Read.All (Application)",
            "User.Read.All (Application)"
        ]
    }
    
    print("STEP 1: Create App Registration in Azure Portal")
    print("-" * 80)
    print("1. Go to: https://portal.azure.com")
    print("2. Navigate to: Azure Active Directory > App registrations")
    print("3. Click: 'New registration'")
    print("4. Enter Name: 'Planner MCP Server'")
    print("5. Select: 'Accounts in this organizational directory only (Single tenant)'")
    print("6. Click: 'Register'")
    print()
    
    print("STEP 2: Configure API Permissions")
    print("-" * 80)
    print("1. In your new app registration, go to: 'API permissions'")
    print("2. Click: 'Add a permission'")
    print("3. Select: 'Microsoft Graph'")
    print("4. Add the following permissions:")
    for perm in required_permissions["Microsoft Graph API Permissions"]:
        print(f"   - {perm}")
    print("5. Click: 'Grant admin consent for [Your Organization]'")
    print()
    
    print("STEP 3: Create Client Secret")
    print("-" * 80)
    print("1. Go to: 'Certificates & secrets'")
    print("2. Click: 'New client secret'")
    print("3. Add description: 'MCP Server Secret'")
    print("4. Select expiration: '24 months' (recommended)")
    print("5. Click: 'Add'")
    print("6. **IMPORTANT**: Copy the secret value immediately (it won't be shown again)")
    print()
    
    print("STEP 4: Gather Required Information")
    print("-" * 80)
    print("From your app registration, copy the following:")
    print("1. Application (client) ID - from the 'Overview' page")
    print("2. Directory (tenant) ID - from the 'Overview' page")
    print("3. Client secret value - from step 3 above")
    print()
    
    print("STEP 5: Configure Environment Variables")
    print("-" * 80)
    print("Create a .env file in your project root with:")
    print()
    print("AZURE_TENANT_ID=your-tenant-id")
    print("AZURE_CLIENT_ID=your-client-id")
    print("AZURE_CLIENT_SECRET=your-client-secret")
    print()
    
    print("=" * 80)
    print("Setup complete! You can now run the MCP server.")
    print("=" * 80)
    
    manifest = {
        "displayName": "Planner MCP Server",
        "signInAudience": "AzureADMyOrg",
        "requiredResourceAccess": [
            {
                "resourceAppId": "00000003-0000-0000-c000-000000000000",
                "resourceAccess": [
                    {"id": "8b3c1b15-fb51-4b0b-b6d5-64a560392a8e", "type": "Scope"},
                    {"id": "89fe9824-0a47-4dfa-92a5-a5597d175a70", "type": "Scope"},
                    {"id": "5b567255-7703-4780-807c-7be8301ae99b", "type": "Role"},
                    {"id": "df021288-bdef-4463-88db-98f22de89214", "type": "Role"}
                ]
            }
        ]
    }
    
    with open("azure_app_manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
    
    print("\nApp manifest saved to: azure_app_manifest.json")


if __name__ == "__main__":
    main()
