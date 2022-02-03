import servicenow.selenium_scrape as sel
import os


def logon():
    output_dir = os.path.join(__file__, '..', '..', 'output')
    print(os.path.abspath(output_dir))
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)
    okta_url = 'https://taihooncology.okta.com/'
    svc_now_url = 'https://tizona.service-now.com/fna/'
    sess = sel.SessionMgmt()
    remote_driver = sess.start_session()
    remote_driver.get(okta_url)
    input("Log on to Okta then press any key:")
    remote_driver.get(svc_now_url)
    input("Make sure that you are logged on to service now. Press any key after that.")


if __name__ == '__main__':
    logon()