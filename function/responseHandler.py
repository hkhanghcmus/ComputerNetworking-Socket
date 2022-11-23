import config


def getLengthOfContent(resHeader):
    indexStart = resHeader.find(b"Content-Length") + len(b"Content-Length: ")
    indexEnd = resHeader.find(b"\r\n",indexStart)
    if indexEnd == -1:
        indexEnd = len(resHeader)
    return int(resHeader[indexStart:indexEnd])

def getContentType(resHeader):
    indexStart = resHeader.find(b"Content-Type") + len(b"Content-Type: ")
    indexEnd = resHeader.find(b";",indexStart)
    if indexEnd == -1:
        indexEnd = len(resHeader)
    return resHeader[indexStart:indexEnd].decode()

def getContent(client, resHeader, total):
    data = b""
    # xu ly buffer size cho nay
    # Voi content-type: text/html -> file be -> buff chi can 1KB moi lan la du
    # Voi content-type loai khac -> file to -> tang buff size len
    contentType = getContentType(resHeader)
    contentLength = getLengthOfContent(resHeader)

    print(contentType, contentLength, total)
    print(contentLength, contentType)

    match contentType:
        case "text/html":
            buff = config.BUFFER_SIZE
            while total < contentLength:
                res = client.recv(buff)
                data += res
                total += len(res)
        case _: #default
            buff = 50*config.BUFFER_SIZE
            while total < contentLength:
                res = client.recv(buff)
                data += res
                total += len(res)
    return data

def getContent_chunked(client,resHeader,content):
    contentType = getContentType(resHeader)
    buff_size = config.BUFFER_SIZE
    if (contentType != b"text/html"):
        buff_size = 50*config.BUFFER_SIZE
    
    data = b""
    rec = content
    while True:
        chunk_data = b""
        # get data for the first time
        if not rec:
            rec = client.recv(buff_size)
        # Split chunk-length && chunk-data
        splitChunk = rec.split(b"\r\n", 1)
        chunk_leng16 = splitChunk[0]                    # chunk-length in hex
        chunk_leng10 = int(chunk_leng16.decode(), 16)   # conver to decimal for calculate
        chunk_data = splitChunk[1]
        
        # End of download
        if chunk_leng10 == 0:
            break
        # If it not have enough chunk-data -> get more
        while len(chunk_data) < chunk_leng10:
            chunk_data += client.recv(buff_size)
     
        # Add chunk-data to data
        data += chunk_data[:chunk_leng10]
        # Give data remaining in chunk-data for the next chunk (loop)
        rec = chunk_data[chunk_leng10 + 2:]

    return data

def getHeader(client):
    splitStr = b"\r\n\r\n"
    data = b""
    while data.find(splitStr) == -1:
        data += client.recv(config.BUFFER_SIZE)
    
    indexStartContent = data.find(splitStr)
    #Lay Header
    resHeader = data[:indexStartContent]
    #Lay data con lai sau khi loai bo header
    data = data[indexStartContent + 4:]
    
    return resHeader, data

def getResponse(client):
    resHeader, data = getHeader(client)
    #Kiem tra Header co can su dung chunked hay khong
    if (resHeader.find(b"Transfer-Encoding: chunked") == -1):
        # Xu li content length
        total = len(data)
        data += getContent(client,resHeader,total)
        checkChunked = False
    else:
        # Xu li chunked
        data = getContent_chunked(client,resHeader,data)
        checkChunked = True
        
    return data, checkChunked