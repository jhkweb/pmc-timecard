import pyad.adquery


def get_user_title(name):
    q = pyad.adquery.ADQuery()
    q.execute_query(
        attributes=["name", "title"],
        where_clause="name = '{}'".format(name),
        base_dn="OU=Users, OU=JHK, DC=jhkelly, DC=com"
    )
    for row in q.get_results():
        if row['title']:
            return row['title']
        else:
            return False


def get_user_mail(name):
    q = pyad.adquery.ADQuery()
    q.execute_query(
        attributes=["name", "mail"],
        where_clause="name = '{}'".format(name),
        base_dn="OU=Users, OU=JHK, DC=jhkelly, DC=com"
    )
    for row in q.get_results():
        if row['mail']:
            return row['mail']
        else:
            return False
