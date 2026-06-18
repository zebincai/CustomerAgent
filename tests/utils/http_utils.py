def parse_response(rsp):
    if rsp.status_code != 200:
        print(f"""\n=======>>>
Network Error:
Statu Code:  {rsp.status_code}
Error Info:
{rsp.text}""")
        return rsp.text
    else:
        print(rsp.text)
        return rsp.text
