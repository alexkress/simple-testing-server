#!/usr/bin/env python
from BaseHTTPServer import HTTPServer
from BaseHTTPServer import BaseHTTPRequestHandler
import cgi
import random
import os.path
from os import listdir


PORT = 8003
FILE_PREFIX = ""

if __name__ == "__main__":
    try:
        import argparse

        #random.seed()

        parser = argparse.ArgumentParser(description='A simple fake server for testing your API client.')
        parser.add_argument('-p', '--port', type=int, dest="PORT",
                           help='the port to run the server on; defaults to 8003')
        parser.add_argument('--path', type=str, dest="PATH",
                           help='the folder to find the json files')

        args = parser.parse_args()

        if args.PORT:
            PORT = args.PORT
        if args.PATH:
            FILE_PREFIX = args.PATH

    except Exception:
        # Could not successfully import argparse or something
        pass


class JSONRequestHandler (BaseHTTPRequestHandler):

    def do_GET(self):

        folder_path=FILE_PREFIX + "/" + self.path[1:]
        response_content_type="Content-type", "application/json"
        
        http_code=200

        is_file=True
        file_path=folder_path
        if os.path.isfile(folder_path+ ".json"):
	        file_path=folder_path+ ".json"
        elif os.path.isfile(file_path):
			#figure out content type
			extension=os.path.splitext(file_path)[1]
			if extension==".html" or extension==".htm":
				response_content_type="text/html"
			elif extension==".css":
				response_content_type="text/css"
			elif extension==".js":
				response_content_type="text/javascript"
			else:
				response_content_type="text/plain"
        else:
		    is_file=False
		
        if is_file:
            try:
                output = open(file_path, 'r').read()
            except Exception:
                output = "{'error': 'Could not find file " + file_path + "}"
                http_code=404
        elif os.path.isdir(folder_path):
            only_files = [ f for f in listdir(folder_path) if os.path.isfile(os.path.join(folder_path,f)) ]
            output='[\n'
            is_first=True
            for f in only_files:
                if os.path.splitext(f)[1] == '.json':
                    output+=('' if is_first else ',\n')+'%s' % (os.path.splitext(f)[0])
                    is_first=False
            output+=']\n'
        else:
            http_code=404
            output='{"error":"path does not exist"}'


        #send response code:
        self.send_response(http_code)
        #send headers:
        self.send_header("Content-type", response_content_type)
        # send a blank line to end headers:
        self.wfile.write("\n")

        self.wfile.write(output)

    def do_POST(self):

        error=''
        
        if self.path == "/success":
            response_code = 200
        elif self.path == "/error":
            response_code = 500
        else:
            try:
                response_code = int(self.path[1:])
            except Exception:
                response_code = 201
            
        try:
            self.send_response(response_code)
            self.wfile.write('Content-Type: application/json\n')
            self.wfile.write('Client: %s\n' % str(self.client_address))
            self.wfile.write('User-agent: %s\n' % str(self.headers['user-agent']))
            self.wfile.write('Path: %s\n' % self.path)
            
            self.end_headers()

            form = cgi.FieldStorage(
                    fp=self.rfile, 
                    headers=self.headers,
                    environ={'REQUEST_METHOD':'POST',
                                     'CONTENT_TYPE':self.headers['Content-Type'],
                                     })

            object_id = random.randint(0, 500000000)

            try:
                #also write to disk
                file_path=FILE_PREFIX + "/" + self.path[1:] +"/" + str(object_id) + ".json"
                disk_storage = open (file_path, 'a')
            except Exception as e:
                error='can\'t create file at %s' % (file_path)
                raise

            self.wfile.write('{\n"id":%i' % object_id)
            disk_storage.write('{\n"id":%i' % object_id)
            for field in form.keys():
                    json_line=',\n"%s":"%s"' % (field, form[field].value)
                    self.wfile.write(json_line)
                    disk_storage.write(json_line)
            self.wfile.write('\n}')
            disk_storage.write('\n}')
            disk_storage.close

                            
        except Exception as e:
            self.send_response(500)
            self.wfile.write(error)
            raise


server = HTTPServer(("localhost", PORT), JSONRequestHandler)
server.serve_forever()
