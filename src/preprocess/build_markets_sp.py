import pandas as pd
import numpy as np
import copy


def _filter_markets_hoo(
        markets_hoo
    ):
    # Rename properly in Agency Name
    markets_hoo["Agency Name"] = (markets_hoo["Agency Name"]
                                  .str.replace(r'^\d+-\w+-\d+\s*', '', regex=True)
                                  .str.strip())
    # I want to remove last numbers and get only last 2 characters
    #  from the string in the column 'Shipping Address'
    markets_hoo['Agency Region'] = (markets_hoo['Shipping Address']
                                    .str.replace(r'\s*\d+$', '', regex=True)
                                    .str[-2:])
    # Setting default values for new columns
    markets_hoo['By Appointment Only'] = "No"
    markets_hoo['Status'] = 'Active'
    markets_hoo["Is Market"] = True
    return markets_hoo


def _filter_shopping_partners_hoo(
        shopping_partners_hoo
    ):
    shopping_partners_hoo["Is Market"] = False
    shopping_partners_hoo.rename(columns={
        'Name': 'Agency Name',
        'External ID': 'Agency ID',
        'Monthly Options': 'Frequency',
        }, inplace=True)
    return shopping_partners_hoo


def _squeeze_wrap_around_services(
        sp_wrap_serv
    ):
    # All wraparound services in a single cell for each agency
    SP_services = sp_wrap_serv.groupby('Agency ID')[
        'Wraparound Service'
    ].apply(lambda x: ', '.join(x)).reset_index()
    SP_wrap_services = sp_wrap_serv.copy()
    SP_wrap_services.drop(columns=['Wraparound Service'], inplace=True)

    # Merge wraparound services list with the original data
    SP_wrap_services = pd.merge(
        SP_wrap_services, SP_services, 
        on='Agency ID', 
        how='left'
    )
    SP_wrap_services.drop_duplicates(inplace=True)

    return SP_wrap_services


def main():
    # Load the data from Excel files
    markets_hoo = pd.read_excel('CAFB_Markets_HOO.xlsx')
    markets_cultures = pd.read_excel('CAFB_Markets_Cultures_Served.xlsx')
    markets_wrap_serv = pd.read_excel('CAFB_Markets_Wraparound_Services.xlsx')

    sp_hoo = pd.read_excel('CAFB_Shopping_Partners_HOO.xlsx')
    sp_cultures = pd.read_excel('CAFB_Shopping_Partners_Cultures_Served.xlsx')
    sp_wrap_serv = pd.read_excel('CAFB_Shopping_Partners_Wraparound_Services.xlsx')

    # Filter and clean the data
    markets_hoo = _filter_markets_hoo(markets_hoo)
    sp_hoo = _filter_shopping_partners_hoo(sp_hoo)

    # Concatenate markets and shopping partners HOO
    """
    >>> set(sp_hoo.columns) - set(markets_hoo.columns), 
    {'Additional Note on Hours of Operations',
    'Date of Last Verification',
    'Last SO Create Date',
    'Phone', 
    'County/Ward'},

    >>> set(markets_hoo.columns) - set(sp_hoo.columns),
    {'Choice Options '})
    """
    markets_sp_hoo = pd.concat(
        [markets_hoo, sp_hoo], 
        ignore_index=True
    )

    # Concatenate markets and shopping partners cultures served 
    sp_cultures.rename(
        columns={'Company Name': 'Agency Name'}, 
        inplace=True
    )
    markets_sp_cultures = pd.concat(
        [markets_cultures, sp_cultures], 
        ignore_index=True
    )

    # Squeeze wraparound services into single cells for each agency
    markets_wrap_services = _squeeze_wrap_around_services(
        markets_wrap_serv
    )
    sp_wrap_services = _squeeze_wrap_around_services(
        sp_wrap_serv
    )
    # Concatenate markets and shopping partners wraparound services
    markets_sp_wrap_services = _squeeze_wrap_around_services(
        pd.concat(
            [markets_wrap_services, sp_wrap_services], 
            ignore_index=True
        )
    )

    # Merge markets and shopping partners HOO and cultures served
    maskets_sp_hoo_cultures = pd.merge(
        markets_sp_hoo, markets_sp_cultures, 
        on="Agency ID", 
        how='outer'
    )
    # Set names and agency ids 
    maskets_sp_hoo_cultures["Agency Name"] = maskets_sp_hoo_cultures["Agency Name_x"]
    maskets_sp_hoo_cultures.loc[
        maskets_sp_hoo_cultures["Agency Name"].isna(), "Agency Name"
    ] = maskets_sp_hoo_cultures["Agency Name_y"]
    maskets_sp_hoo_cultures.drop(
        columns=["Agency Name_x", "Agency Name_y"], inplace=True
    )

    # Merge markets and shopping partners HOO_cultures and wraparound services
    markets_sp = pd.merge(
        maskets_sp_hoo_cultures, markets_sp_wrap_services, 
        on="Agency ID", 
        how='outer'
    )
    # Set names and agency ids
    markets_sp["Agency Name"] = markets_sp["Agency Name_x"]
    markets_sp.loc[
        markets_sp["Agency Name"].isna(), "Agency Name"
    ] = markets_sp["Agency Name_y"]
    markets_sp.drop(
        columns=["Agency Name_x", "Agency Name_y"], 
        inplace=True
    )

    # Tabular view
    columns = list(markets_sp.columns)
    columns.remove("Agency Name")
    columns.remove("Agency ID")
    markets_sp = markets_sp[["Agency ID", "Agency Name"] + columns]
    markets_sp.to_excel("CAFB_Markets_Shopping_Partners.xlsx", index=False)


if __name__ == "__main__":
    main()