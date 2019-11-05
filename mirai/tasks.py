from mirai_project.celery import app
from dsmirai import linux_container_creation, sct_control, rat_control

@app.task
def lxc_creation(container_id):
    print(container_id)
    return linux_container_creation.create(container_id)

@app.task
def lxc_migration(container, iaas=None):
    from dsmirai import linux_container_migration
    return linux_container_migration.migrate(container, iaas)

@app.task
def api_rat(iaas):
    rat_control.rat_trigger(iaas)

@app.task
def api_sct(iaas):
    sct_control.sct_trigger(iaas)
