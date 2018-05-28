import requests
requests.packages.urllib3.disable_warnings()
import time
import sys

#input user to be configured, username, password
#      sbxid to be configued    
def login(url_base):
    login_url = url_base + 'api/mo/aaaLogin.xml'
    s = requests.session()
    #login using admin cred
    data = "<aaaUser name='{0}' pwd='{1}'/>".format(admin_user, admin_password)
    try:
        r = s.post(login_url, data=data, verify=False)
    except Exception,e:
        pass
    print(r.text)
    return s
    
def add_user(session, url_base, username, password, sbxid):
    useradd_url = url_base + 'api/policymgr/mo/uni/userext.xml'
    domainref_url = url_base + '/api/mo/uni/tn-kubesbx05.xml'   
    s = session
    
    #add security domain into the tenant
    data = '<fvTenant name="kube{0}"><aaaDomainRef name="{0}"/></fvTenant>'.format(sbxid)
    try:
        r = s.post(domainref_url, data=data, verify=False)
    except Exception,e:
        pass
    print(r.text)
    time.sleep(1)    

    #create the user using the security doamin
    data = '''<aaaUser name="{0}" phone="" pwd="{1}" >
            <aaaUserDomain childAction="" descr="" name="{2}"  status="">
                <aaaUserRole childAction="" descr="" name="{2}" privType="writePriv"/>
            </aaaUserDomain>
      </aaaUser>'''.format(user, password, sbxid)
    try:
        r = s.post(useradd_url, data=data, verify=False)
    except Exception,e:
        pass
    return r.text
    

def del_user(session, url_base, username):
    userdel_url = url_base + 'api/mo/uni/userext/user-{0}.xml'.format(username)
    s = session
    try:
        r = s.delete(userdel_url)
    except Exception,e:
        pass
    return r.text
    
if __name__ == "__main__":
    action = sys.argv[1]
    if action == 'add':
        sbxid = sys.argv[2]
        user = sys.argv[3]
        password = sys.argv[4]
    else:
        user = sys.argv[2]
    
    admin_user = 'admin'
    admin_password = 'Adm!n123!'
    
    url_base = 'https://10.10.20.12/'
    s = login(url_base)
    time.sleep(1)
    
    if action == 'add':
        print(add_user(s, url_base, user, password, sbxid))
    else:
        print(del_user(s, url_base, user))
        
        
