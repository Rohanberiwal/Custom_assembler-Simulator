mem = {}
halted = False

opcode_identifier = {
    "00000": "add",
    "00001": "sub",
    "00010": "movB",
    "00011": "mov",
   "00100":  "ld",
   "00101":  "st",
    "00110": "mul",
    "00111": "div",
   "01000":  "rs",
   "01001":  "ls",
    "01010": "xor",
   "01011":  "or",
    "01100": "and",
    "01101": "not",
    "01110": "cmp",
    "01111": "jmp",
    "11100": "jlt",
    "11101": "jgt",
   "11111":  "je",
    "11010": "hlt",
}

# create a dictionary of registers
register_value = {
    "000": 0,
    "001": 0,
    "010": 0,
    "011": 0,
    "100": 0,
    "101": 0,
    "110": 0,
    "111": "0"*16
}

def toBin(num, bits = 7):
    num = int(num)
    ans = ""
    if num == 0:
        ans = "0"
    else:
        while num > 0:
            ans = str(num % 2) + ans
            num = num // 2

    leftBits = bits - len(ans)
    if leftBits > 0:
        padd = "0" * leftBits
        ans = padd + ans

    return ans

def toDec(Bstr):
    num=list(Bstr)
    ans=0
    n=len(num)
    i=0
    while(i!=n):
        if num[n-i-1]=='1':
            ans+=2**i
            i+=1
        else:
            i+=1
            continue
    return ans

def reset_flags():
    global register_value
    register_value["111"] = '0'*16

def set_O():
    global register_value
    temp_flag = register_value["111"]
    register_value["111"] = temp_flag[0:12]+'1'+temp_flag[13:]

def set_L():
    global register_value
    temp_flag = register_value["111"]
    register_value["111"] =  temp_flag[0:13]+'1'+temp_flag[14:]

def set_G():
    global register_value
    temp_flag = register_value["111"]
    register_value["111"] =  temp_flag[0:14]+'1'+temp_flag[15:]

def set_E():
    global register_value
    temp_flag = register_value["111"]
    register_value["111"] =  temp_flag[0:15]+'1'


def file_loader() -> list:
    """
          Load all lines at once, the strip the newline character ,
          then remove any  null strings from the list of lines
    """

    all_lines = []
    
    import sys
    for i in sys.stdin:
        all_lines.append(i)

    # Strip newline character
    all_lines = [line.strip('\n') for line in all_lines]

    # Strip tabs
    all_lines = [line.replace('\t'," ") for line in all_lines]
    # NOT REMOVING NULL STRINGS to maintain line tracking
    # Remove null strings from the list
    #all_lines = list(filter(None, all_lines))

    return all_lines

def file_loader2(file_name: str = 'test.txt') -> list:
    """
            Load all lines at once, the strip the newline character ,
            then remove any  null strings from the list of lines
        """

    all_lines = []
    with open(file_name, "r") as f:
        all_lines = f.readlines()
        
    # Strip newline character
    all_lines = [line.strip('\n') for line in all_lines]

    # Strip tabs
    all_lines = [line.replace('\t'," ") for line in all_lines]

    # NOT REMOVING NULL STRINGS to maintain line tracking
    # Remove null strings from the list
    all_lines = list(filter(None, all_lines))

    return all_lines

def err_gen(err_str: str):
    print(err_str)
    exit()

def init_mem(all_lines: str):

    # initialise all 128 lines to 16bit zeros
    for idx in range(0,128):
        mem[toBin(idx)] = '0'*16


    # Now we load the data from stdin's buffer
    for idx in range(0,len(all_lines)):
        data = all_lines[idx]

        # If data/instr is not 16bit throw error.
        if len(data) != 16:
            err_gen(f'Error Instruction not of 16bits')
        
        # Otherwise put it in dictionary
        mem[toBin(idx)] = data
        
    
def fetchData(Prog_count):
    
    # If program counter's bit string is not 7 throw error
    if len(Prog_count) != 7:
        err_gen(f'Program counter is not 7bit')
    
    # otherwise return the instruction at given memory location
    return mem[Prog_count]


def process_A_type(instr_str: str, opcode:str):

    # Extract register address from the binary
    reg3_addr = opcode[-3:]
    reg2_addr = opcode[-6:-3]
    reg1_addr = opcode[-9:-6]

    #print(f'R1={reg1_addr} R2={reg2_addr} R3={reg3_addr} \n {opcode}')

    # Get value at register 2 and 3 (used for computation)
    global register_value
    reg2_val = register_value[reg2_addr]
    reg3_val = register_value[reg3_addr]

    # Explicity convert values to integers before loading them in Reg3
    if instr_str == 'add':
        temp_data = int(reg2_val + reg3_val)

        # highest value below which register can store value 
        # aka highest possible 16bit value in decimal
        if temp_data < 65536:
            register_value[reg1_addr] = temp_data
        else:
            set_O()
            register_value[reg1_addr] = 0
        

    elif instr_str == 'sub':

        # negative value means overflow and set reg1 = 0
        if reg3_val > reg2_val:
            set_O()
            register_value[reg1_addr] = 0
        elif reg3_val < reg2_val:
            register_value[reg1_addr] = int(reg2_val - reg3_val)


    elif instr_str == 'mul':
        temp_data = reg2_val*reg3_val
        if temp_data < 65536:
            register_value[reg1_addr] = temp_data
        else:
            set_O()
            register_value[reg1_addr] = 0
    
    elif instr_str == 'xor':
        register_value[reg1_addr] = reg2_val ^ reg3_val

    elif instr_str == 'or':
        register_value[reg1_addr] = reg2_val | reg3_val
    
    elif instr_str == 'and':
        register_value[reg1_addr] = reg2_val & reg3_val


def process_B_type(instr_str: str, opcode:str):
    
    # Extract the register address and imm value
    reg1_addr = opcode[-10:-7]
    imm = toDec(opcode[-7:])
    toShift = toBin(register_value[reg1_addr], 16)
    shiftBy = "0"*imm

    if instr_str == 'movB':
        register_value[reg1_addr] = imm
        #print(f'Reg addr = {reg1_addr} IMM = {imm} {opcode}')

    elif instr_str == 'rs':
        temp_data = shiftBy + toShift
        temp_data = temp_data[0:16]
        register_value[reg1_addr] = toDec(temp_data)

    elif instr_str == 'ls':
        temp_data = toShift + shiftBy
        temp_data = temp_data[-16:]
        register_value[reg1_addr] = toDec(temp_data)


def process_C_type(instr_str: str, opcode:str):
    
    reg1_addr = opcode[-6:-3]
    reg2_addr = opcode[-3:]

    if instr_str == 'mov':
        register_value[reg2_addr] = register_value[reg1_addr]
    
    elif instr_str == 'div':
        # If R2 is zero then set overflow flag and set R0 R1 to zero
        if register_value[reg2_addr] == 0:
            set_O()
            register_value['000'] = '0'*16
            register_value['001'] = '0'*16
        else:
            quo = register_value[reg1_addr] // register_value[reg2_addr]
            rem = register_value[reg1_addr] % register_value[reg2_addr]
            register_value['000'] = quo
            register_value['001'] = rem
    
    elif instr_str == "not":
        register_value[reg1_addr] = ~register_value[reg2_addr]
    
    elif instr_str == 'cmp':

        reg1_val = register_value[reg1_addr]
        reg2_val = register_value[reg2_addr]

        if reg1_val < reg2_val:
            set_L()
        elif reg1_val > reg2_val:
            set_G()
        elif reg1_val == reg2_val:
            set_E()


def process_D_type(instr_str: str, opcode:str):
    
    reg1_addr = opcode[-10:-7]
    mem_addr = opcode[-7:]

    if instr_str == 'ld':
        register_value[reg1_addr] = toDec(fetchData(mem_addr))
    elif instr_str == 'st':
        mem[mem_addr] = toBin(register_value[reg1_addr], 16)

def process_E_type(instr_str: str, opcode:str, prog_counter: str):

    mem_addr = opcode[-7:]

    if instr_str == 'je' and register_value["111"][-1] == 1:
        return mem_addr
    
    if instr_str == 'jgt' and register_value["111"][-2] == 1:
        return mem_addr
    
    if instr_str == 'jlt' and register_value["111"][-3] == 1:
        return mem_addr
    
    if instr_str == 'jmp':
        return mem_addr
    
    return get_new_pc(prog_counter)
    

def process_F_type(instr_str: str, opcode:str):
    global halted
    halted = True


def get_new_pc(prog_counter) -> str:
    """
    Convert the 7bit address to decimal
    then add +1 for next line
    convert new address to 7bit binary
    return it
    """
    curr_line = toDec(prog_counter)
    return toBin(curr_line+1)


def EE_execute(instr: str, prog_counter: str):

    # Since we have already checked the length of instruction in init_mem() function,
    # We assume it IS 16 bit now.

    # We extract the opcode
    opcode = instr[:5]
    # Reverse convert binary to assmebly
    instr_str = opcode_identifier[opcode]

    #print(f'{toDec(prog_counter)} {instr_str}')
    
    A_type_instr = ["add", "sub", "mul", "xor", "or", "and"]
    B_type_instr = ["rs", "ls", "movB"]
    C_type_instr = ["div", "not", "cmp", "mov"]
    D_type_instr = ["ld", "st"]
    E_type_instr = ["jmp", "jlt", "jgt", "je"]
    F_type_instr = ["hlt"]

    # by default get the next line in 7 bit as the new address
    next_pc = get_new_pc(prog_counter)
    if instr_str in A_type_instr:
        process_A_type(instr_str, instr[5:])
    elif instr_str in B_type_instr:
        process_B_type(instr_str, instr[5:])
    elif instr_str in C_type_instr:
        process_C_type(instr_str, instr[5:])
    elif instr_str in D_type_instr:
        process_D_type(instr_str, instr[5:])
    elif instr_str in E_type_instr:
        # This instruction will update the program counter
        next_pc = process_E_type(instr_str, instr[5:], prog_counter)
    elif instr_str in F_type_instr:
        process_F_type(instr_str, instr[5:])

    return next_pc

if __name__ == '__main__':
    all_lines = file_loader2() # Change it to file_loader() to work with stdin
    init_mem(all_lines)  # initalise memory
    
    prog_counter = '0'*7 # Initialise program counter
    
    while(halted!=True):
        old_pc_dump = prog_counter
        reset_flags()
        instr = fetchData(prog_counter)
        prog_counter = EE_execute(instr, prog_counter)

        # PC + RF dump
        print(f'{old_pc_dump} '+' '.join([str(toBin(rval,16)) for rval in register_value.values()]))

    # Memory dump of enitre 128 lines
    for line in mem.values():
        print(line)
