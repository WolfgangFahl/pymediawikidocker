'''
Created on 2022-10-25

@author: wf
'''

class Logger(object):
    '''
    simple logger
    '''

    @classmethod
    def check_and_log(cls,msg:str,ok:bool)->bool:
        """
        log the given message with the given ok flag
        
        Args:
            msg(str): the message to log/print
            ok(bool): if True show ✅ marker else ❌
            
        Return:
            bool: the ok parameter for fluid syntax
        """
        marker="✅" if ok else "❌"
        print(f"{msg}:{marker}")
        return ok