import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-oca-contract",
    description="Meta package for oca-contract Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-agreement_rebate_partner_company_group>=17.0dev,<16.1dev',
        'odoo-addon-contract>=17.0dev,<16.1dev',
        'odoo-addon-contract_invoice_start_end_dates>=17.0dev,<16.1dev',
        'odoo-addon-contract_payment_mode>=17.0dev,<16.1dev',
        'odoo-addon-contract_sale>=17.0dev,<16.1dev',
        'odoo-addon-contract_sale_generation>=17.0dev,<16.1dev',
        'odoo-addon-contract_variable_quantity>=17.0dev,<16.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 17.0',
    ]
)
