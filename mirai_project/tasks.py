from mirai_project.celery import app
from dsmirai import iaas_deamon
from dsmirai import rat_control
from dsmirai import sct_control
from dsmirai.persistent_model import dashboard_helper
from dsmirai.persistent_model import helpers
from dsmirai import onos_cleaner
from dsmirai import network_evaluator
@app.task
def iaas_daemon():
    iaas_deamon.iaas_discovery()
    return


@app.task
def rat_daemon():
    rat_control.rat_trigger()
    return


@app.task
def sct_daemon(iaas_name=None):
    sct_control.sct_trigger(iaas_name)
    return

@app.task
def iaas_consumption():
    dashboard_helper.iaas_resource_consumption()
    return


@app.task
def clean_onos_env():
    onos_cleaner.clean_onos()
    return


@app.task
def iperf_test():
    network_evaluator.run()
    return 1


@app.task
def bandwidth_live_test():
    network_evaluator.bandwidth_live_evaluator()
    return 1

@app.task
def db_cleaner():
    helpers.db_cleaner_()
    return 1
