# WAF-Cloner

This Python script allows you to clone AWS WAF (Web Application Firewall) Web ACLs within the same region or across different regions. It provides a simple command-line interface to select source and target regions, choose a source Web ACL, and create a clone with a new name and description.

## Features

- Clone Web ACLs within the same region or across different regions
- Support for both Regional and CloudFront (Global) Web ACLs
- Handles region-specific rules (e.g., IP sets) appropriately
- Sanitizes input to ensure valid Web ACL names
- Uses AWS profiles for secure credential management

## Prerequisites

- Python 3.6 or higher
- Boto3 library (`pip install boto3`)
- AWS CLI configured with profiles for the accounts you want to use

## Usage

1. It's pretty straightforward. Just clone the repo.
2. Execute the python file by simple `python3 waf-cloner.py
3. Follow the prompts to select:
- AWS profile
- Source region
- Target region
- Source Web ACL
- New Web ACL name and description

## Supported Regions

By default, the script supports two regions:
- ap-south-1 (Mumbai) for Regional Web ACLs
- us-east-1 (N. Virginia) for CloudFront (Global) Web ACLs

To add or modify supported regions:

1. Open the `waf_cloner.py` file.
2. Locate the `select_region` function.
3. Modify the `regions` list to include your desired regions. For example:

```
regions = [
    ("1", "ap-south-1", "Mumbai (Regional)"),
    ("2", "us-east-1", "N. Virginia (Global)"),
    ("3", "eu-west-1", "Ireland (Regional)"),
    # Add more regions as needed
]
```

## Limitations
1. The script skips rules that reference rule groups, as these can't be directly cloned.
2. When cloning between different regions, rules referencing IP sets are skipped.
3. Custom responses in rules are removed during cloning.
4. You may need to manually adjust some rules or recreate certain configurations after cloning, especially for cross-region clones.
