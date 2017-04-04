# import used libraries
import http.client, urllib.request, urllib.parse, urllib.error
import base64, json, sys, os, threading

def load_url(url, filename, filesystem_lock):
    try:
        # open connection to URL
        socket = urllib.request.urlopen(url)
        # read data
        data = socket.read()
        # close connection
        socket.close()
    # on all exceptions
    except:
        print("error loading", url)
    # if no exceptions
    else:
        # save loaded data
        save_to_file(data, filename, filesystem_lock)
        
def save_to_file(data, filename, filesystem_lock):
    # wait for file system and block it
    filesystem_lock.acquire()
    try:
        # while already have file with this name        
        while os.path.isfile(filename):
            # append '_' to the beginning of file name
            filename = os.path.dirname(filename) + "/_" + os.path.basename(filename)
        with open(filename, 'wb') as f:
            # and save data
            f.write(data)
            f.close()
    except:
        print("error saving", filename)
    # release file system
    filesystem_lock.release()
    

def main():
    # Bing search URL
    SERVICE_URL = "https://api.cognitive.microsoft.com/bing/v5.0/images/search"
    # request parameters dictionary (will append to SERVICE_URL) 
    params = {}
    headers = {
        # Request headers
        'Content-Type': 'multipart/form-data',
        'Ocp-Apim-Subscription-Key': 'e6a9f93108d04a1c874af27da7f77ac9',
    }
    params["count"]   = 8
    params["offset"]  = 0
    params["mkt"]       = "en-us"

    # try to read command line parameters
    try:
        params["q"] = sys.argv[1]
        images_count = int(sys.argv[2])
        
    # if have less than 2 parameters (IndexError) or
    # if second parameter cannot be cast to int (ValueError)
    except (IndexError, ValueError):
        # print usage string
        print("Bing image search tool")
        print("Usage: bing.py search_str images_count")
        # end exit
        return 1

    # make directory at current path
    dir_name = "./" + params["q"] + "/"
    if not os.path.isdir(dir_name):
        os.mkdir(dir_name)
        
    # list to store loading threads
    loaders = []
    # file system lock object
    filesystem_lock = threading.Lock()
    number_name = 0
    
    try:
        # loop for images count
        while(params["offset"] < images_count):
            # combine URL string, open it and parse with JSON
            conn = http.client.HTTPSConnection('api.cognitive.microsoft.com')
            conn.request("POST", "/bing/v5.0/images/search?%s" % urllib.parse.urlencode(params), "{body}", headers)
            response = conn.getresponse()
            string = response.read().decode('utf-8')
            dataresponse = json.loads(string)
            # if current search offset greater or equal to returned total files  
            if params["offset"] >= dataresponse["totalEstimatedMatches"]:
                # then break search loop
                break
            # extract image results section 
            results = dataresponse["value"]
            # loop for results
            for result in results:
                # extract image URL
                image_url = result["contentUrl"]
                #print(image_url)
                # create new loading thread  
                loader = threading.Thread(\
                    target = load_url,\
                    args=(\
                          image_url,\
                          dir_name + os.path.basename(str(number_name)+".jpg"),\
                          filesystem_lock))
                number_name += 1
                # start loading thread
                loader.start()
                # and add it to loaders list
                loaders.append(loader)
                # advance search offset
                params["offset"] += 1
                # break if no more images needed
                if params["offset"] >= images_count:
                    break;            
            conn.close()
    # on all exceptions
    except:
        print("Error occured")
        return 1
    
    # wait for all loading threads to complete 
    for loader in loaders:
        loader.join()

    # all done
    print("done")
    return 0;

if __name__ == '__main__':
    status = main()
    sys.exit(status)