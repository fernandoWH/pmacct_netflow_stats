from django.shortcuts import render
from django.http import HttpResponse
from pmacct_netflow.env import env
from django.views.decorators.csrf import csrf_exempt
import pymysql
from pymysql.cursors import DictCursor
import re
import os


@csrf_exempt
def index(request):
    return render(request, 'report/report.html')


@csrf_exempt
def submit(request):
    zone = request.POST['zone']
    day = request.POST['day']
    timeon = request.POST['timeon'] + ":00"
    timeoff = request.POST['timeoff'] + ":00"
    table = "acct_v9_" + day

    if timeoff <= timeon:
        return HttpResponse("Время начала перида больше времени окончания периода!")

    creds = env()
    sudoPassword = creds.root_pass
    connection = pymysql.connect(
        host=creds.mysql_host,
        user=creds.mysql_user,
        password=creds.mysql_pass,
        db='pmacct',
        charset='utf8mb4',
        cursorclass=DictCursor
    )

    cursor = connection.cursor()
    COMMAND = "SELECT tag, zone FROM devices WHERE zone = " + zone + ";"
    cursor.execute(COMMAND)
    row = cursor.fetchone()
    data = []
    while row is not None:
        data.append(row)
        row = cursor.fetchone()

    if len(data) == 0:
        cursor.close()
        connection.close()
        return HttpResponse("Такой зоны не существует!")

    tag_string = "( "
    for elem in data:
        tag_string = tag_string + "tag=" + str(elem['tag']) + ' or '
    tag_string = re.sub("or $", ")", tag_string)

    COMMAND = "SELECT stamp_updated FROM " + table + " LIMIT 1;"
    cursor.execute(COMMAND)
    row = cursor.fetchone()
    data = []
    while row is not None:
        data.append(row)
        row = cursor.fetchone()

    if len(data) == 0:
        cursor.close()
        connection.close()
        return HttpResponse("Таблица за этот день пуста!")

    free_buffers(sudoPassword)

    timeon = re.sub("[0-9]{2}:[0-9]{2}:[0-9]{2}", timeon, str(data[0]['stamp_updated']))
    timeoff = re.sub("[0-9]{2}:[0-9]{2}:[0-9]{2}", timeoff, str(data[0]['stamp_updated']))
    time_string = "stamp_updated > \'" + timeon + "\' AND stamp_updated < \'" + timeoff + "\'"
    COMMAND = "SELECT ip_src, ip_dst, port_src, port_dst, ip_proto, bytes, stamp_inserted, stamp_updated FROM " + table +" WHERE " \
              + tag_string + " AND " + time_string + " " \
              "ORDER BY bytes DESC LIMIT 20;"
    cursor.execute(COMMAND)
    row = cursor.fetchone()
    data = []
    while row is not None:
        data.append(row)
        row = cursor.fetchone()

    cursor.close()
    connection.commit()
    connection.close()

    free_buffers(sudoPassword)

    html = '<table>\n<tr><th>SRC_IP</th><th>DST_IP</th><th>SRC_PORT</th><th>DST_PORT</th><th>IP PROTO</th><th>BYTES</th><th>INSERTED</th><th>UPDATED</th></tr>\n'
    for elem in data:
        html += "\n<tr>\n"
        for i in elem:
            if i == "bytes" and elem[i] > 200000:
                html = html + '<td style="background-color: rgb(229, 172, 14)">' + str(elem[i]) + '</td>'
            else:
                html = html + '<td>' + str(elem[i]) + '</td>'
        html += "\n</tr>\n"
    html += '</table>\n'

    return HttpResponse(html)


def free_buffers(sudoPassword):
    command = '/home/tiskenderov/scripts/free_buffs.sh'
    p = os.system('echo %s|sudo -S %s' % (sudoPassword, command))