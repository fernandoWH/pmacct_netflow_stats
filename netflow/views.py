from django.shortcuts import render
from django.http import HttpResponse
from pmacct_netflow.env import env
import pymysql
from pymysql.cursors import DictCursor


def index(request):
    try:
        site = request.GET['site']
    except:
        return render(request, 'netflow/man.html')

    html = render_response(site)
    return HttpResponse(html)


def render_response(site):
    creds = env()
    connection = pymysql.connect(
        host=creds.mysql_host,
        user=creds.mysql_user,
        password=creds.mysql_pass,
        db='pmacct',
        charset='utf8mb4',
        cursorclass=DictCursor
    )

    cursor = connection.cursor()
    COMMAND = "SELECT * FROM devices WHERE site='" + site +"';"
    cursor.execute(COMMAND)
    row = cursor.fetchone()
    devices = []
    while row is not None:
        devices.append(row)
        row = cursor.fetchone()


    html = '<!DOCTYPE HTML>' \
           '<html>' \
           '<head>' \
           '<meta http-equiv="refresh" content="30"; charset=utf-8">' \
           '<title>NetFlow</title>' \
           '<style type="text/css">' \
           'TABLE {' \
           'width: 90%;' \
           'background-color: #141619;' \
           'color: white;' \
           'margin: auto;}' \
           'TD {' \
           'background-color: rgba(45, 172, 121, 0.97);' \
           'padding: 8px 25px 8px 25px;' \
           'text-align: center' \
           '}' \
           '</style>' \
           '</head>' \
           '<body>'


    for dev in devices:
        COMMAND = "SELECT ip_src, ip_dst, port_src, port_dst, ip_proto, bytes from acct_v9 WHERE tag = " + \
                  str(dev['tag']) + " AND (NOW() - stamp_updated) < 180 ORDER BY bytes DESC LIMIT 10;"

        cursor.execute(COMMAND)
        row = cursor.fetchone()

        data = []
        while row is not None:
            data.append(row)
            row = cursor.fetchone()

        html += '<table><th><h2>' + dev['device'] + '</h2></th></table><table>\n<tr><th>SRC_IP</th><th>DST_IP</th><th>SRC_PORT</th><th>DST_PORT</th><th>IP PROTO</th><th>BYTES</th></tr>\n'
        for elem in data:
            html += "\n<tr>\n"
            for i in elem:
                if i == "bytes" and elem[i] > 200000:
                    html = html + '<td style="background-color: rgb(229, 172, 14)">' + str(elem[i]) + '</td>'
                else:
                    html = html + '<td>' + str(elem[i]) + '</td>'
            html += "\n</tr>\n"
        html += '</table>\n'




    cursor.close()
    connection.close()

    html += '</body>\n</html>'
    return html