from http.cookiejar import MozillaCookieJar
from argparse import ArgumentParser
import xml.etree.ElementTree as ET
import requests


def make_cookie_file(url, cert_file, key_file, file_name):
    cookiejar = MozillaCookieJar(file_name)
    with requests.Session() as session:
        session.cert = (cert_file, key_file)
        session.cookies = cookiejar
        # Redirection to SSO page
        response1 = session.get(url, timeout=30, verify=False)
        # Get link to SSL authentication
        redirect_url = response1.url.replace('adfs/ls/', 'adfs/ls/auth/sslclient/')
        cert_auth_url = str(redirect_url)
        # Do a request to SSL authentication
        response2 = session.get(cert_auth_url, cookies=cookiejar, verify=False, timeout=30)
        # Parse info from final form
        try:
            tree = ET.fromstring(response2.content)
        except ET.ParseError as e:
            raise e

        form_action = tree.findall("body/form")[0].get('action')
        form_inputs = tree.findall("body/form/input")
        # Get form fields
        form_data = {pair.get('name'): pair.get('value') for pair in form_inputs}
        response3 = session.post(url=form_action, data=form_data, timeout=30)

    cookiejar.save()


if __name__ == '__main__':
    arg_parser = ArgumentParser(description='')
    arg_parser.add_argument('--key')
    arg_parser.add_argument('--cert')
    arg_parser.add_argument('--url')
    arg_parser.add_argument('--output')
    args = arg_parser.parse_args()
    make_cookie_file(args.url, cert_file=args.cert, key_file=args.key, file_name=args.output)
