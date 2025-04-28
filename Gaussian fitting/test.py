import sys,os
from re import match
print('\x1bc\x1b[?7l',end='') #reset and turn off auto-wrap
print('\x1b7',end='') #save cursor
print('\nbefore')
print('\x1b8',end='') #load cursor
print('after\n')
print(f'\x1b[8;{25};{60}t',end='') #resize (rows,columns)
print(os.get_terminal_size())
print('\x1b[6n',end='') #get cursor position
_pos=sys.stdin.read(0)
sys.stdin.flush()
print('s:',_pos,'l:',len(_pos),'s:',str(_pos),'l:',len(str(_pos)),'s:',f'{_pos}','l:',len(f'{_pos}'),end=' end\n')
input('inp:')
print('\x1b[?7h',end='') #turn auto-wrap back on
print(f'\x1b[8;{25};{186}t',end='') #resize (rows,columns)