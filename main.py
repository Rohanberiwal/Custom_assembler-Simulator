import sys
machine_code = []
halt_found = False
label_name_dict = {}

opcodes = {
    "add": "00000",
    "sub": "00001",
    "movB": "00010",
    "mov": "00011",
    "ld": "00100",
    "st": "00101",
    "mul": "00110",
    "div": "00111",
    "rs": "01000",
    "ls": "01001",
    "xor": "01010",
    "or": "01011",
    "and": "01100",
    "not": "01101",
    "cmp": "01110",
    "jmp": "01111",
    "jlt": "11100",
    "jgt": "11101",
    "je": "11111",
    "hlt": "11010",
}

# create a dictionary of registers
register_addr = {
    "R0": "000",
    "R1": "001",
    "R2": "010",
    "R3": "011",
    "R4": "100",
    "R5": "101",
    "R6": "110",
    "FLAGS": "111"
}


def toBin(num, bits):
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


var_addr_dict = {}


def check_var(instr_w_operand, prog_beg_flag, idx) -> bool:

    instr = instr_w_operand[0]
    if instr == 'var' and prog_beg_flag:
        prog_beg_flag = True

        if instr_w_operand[1] in opcodes.keys():
            err_gen(f'Var name cannot be an ISA instruction @{idx+1}')

        if instr_w_operand[1] in label_name_dict.keys():
            err_gen(f'Var name cannot be label name @{idx+1}')

        if instr_w_operand[1] in var_addr_dict.keys():
            err_gen(f'VAR already declared @{idx+1}')

        var_addr_dict[instr_w_operand[1]] = ''  # initialise with no address

    elif instr == 'var' and prog_beg_flag == False:
        err_gen(f'VAR MUST BE AT THE START @{idx+1}')

    if instr != 'var':
        prog_beg_flag = False

    return prog_beg_flag


def clean_list(in_list) -> list:
    # Remove newline, null, space, tabs from list
    out_list = []
    for list_item in in_list:
        if list_item not in ["", "\n", "\t", " "]:
            out_list.append(list_item)

    return out_list


def check_invalid_instr(instr_w_operand, idx):

    instr = instr_w_operand[0]
    # first word is only valid if its a opcode or var or label (With :)
    if instr not in opcodes.keys(
    ) and instr != 'var' and ':' not in instr and instr not in label_name_dict.keys(
    ):
        err_gen(f'INVALID INSTRUCTION at line {idx+1} {instr_w_operand}')


def generate_var_address(last_halt_idx):

    start_addr_line = last_halt_idx - len(var_addr_dict.keys()) + 1

    var_name_list = list(var_addr_dict.keys())
    for idx in range(0, len(var_addr_dict.keys())):
        var_addr_dict[var_name_list[idx]] = toBin(start_addr_line + idx, 7)


def check_hlt(instr_w_operand, prog_end_flag, last_halt_idx, idx) -> list:

    instr = instr_w_operand[0]  # Extract the instruction

    if instr == 'hlt' and prog_end_flag == False:
        prog_end_flag = True
        last_halt_idx = idx

    if last_halt_idx is not None:
        if idx > last_halt_idx:
            err_gen(f'LAST INSTRUCTION NOT HALT @{idx+1}')

    return [prog_end_flag, last_halt_idx]


def sanity_check_micro(instr_w_operand, idx, program_status_list):

    prog_beg_flag = program_status_list[0]
    prog_end_flag = program_status_list[1]
    last_halt_idx = program_status_list[2]

    # removing tabs from all instructions
    instr_w_operand = [
        temp_instr.replace('\t', '') for temp_instr in instr_w_operand
    ]
    instr = instr_w_operand[0]

    # Check all variables are in beginning of the program
    prog_beg_flag = check_var(instr_w_operand, prog_beg_flag, idx)

    return_list = check_hlt(instr_w_operand, prog_end_flag, last_halt_idx, idx)

    prog_end_flag = return_list[0]
    last_halt_idx = return_list[1]

    # Condition for space between label and :
    if ':' in instr_w_operand and instr != ':':
        err_gen(f'INCORRECT LABEL, might have space @{idx+1}')

    # Now scan for label in first instruction itself
    if ':' in instr:
        temp_list = instr.split(':')

        # Check if label is an ISA instruction
        if temp_list[0] in opcodes.keys():
            err_gen(f'ISA instruction cannot be a label! @{idx+1}')

        # Label name cannot be same as varible name
        if temp_list[0] in var_addr_dict.keys():
            err_gen(f'Label name cannot be same as variable name @{idx+1}')

        # check if label exists before
        if temp_list[0] in label_name_dict.keys():
            err_gen(f'Label defined again @{idx+1}')

        # Else add label address and name to dictionary
        else:
            label_name_dict[temp_list[0]] = idx

        if len(instr_w_operand[1:]) > 0:
            program_status_list = sanity_check_micro(instr_w_operand[1:], idx,
                                                     program_status_list)
            prog_beg_flag = program_status_list[0]
            prog_end_flag = program_status_list[1]
            last_halt_idx = program_status_list[2]

    # check if instruction does not belong in ISA
    # CASE SENSITIVE
    check_invalid_instr(instr_w_operand, idx)

    return [prog_beg_flag, prog_end_flag, last_halt_idx]


def update_label_address():
    for label_name in label_name_dict.keys():
        current_idx = label_name_dict[label_name]
        label_name_dict[label_name] = toBin(
            int(current_idx) - len(var_addr_dict.keys()) , 7)


def perform_sanity_checks(list_of_lines: str) -> bool:
    '''
      Check if all var(s) are placed at the beginning of the code.
      and all instruction belong to opcode.'''

    prog_beg_flag = True
    prog_end_flag = False
    last_halt_idx = None
    prog_status_list = [prog_beg_flag, prog_end_flag, last_halt_idx]

    for idx, line in enumerate(list_of_lines):

        if idx >= 128:
            err_gen(
                f'Program length cannot be greater than 127, due to 7bit addressing')

        # Since we have 7bit addressing, program cannot be greater than 127 lines,
        # as 7bit can represents max of 127 lines

        instr_w_operand = line.split(' ')  # Extract first instruction
        instr_w_operand = list(filter(None, instr_w_operand))

        if len(instr_w_operand) != 0:
            prog_status_list = sanity_check_micro(instr_w_operand, idx,
                                                  prog_status_list)

    if prog_status_list[1] == False:
        err_gen(f'Program does NOT have a HLT instruction @{idx+1}')
    # Correctly generate address of variables at the end
    # since now we know the address of last line and total number of variables
    generate_var_address(prog_status_list[-1])

    update_label_address()


def register_addr_validation(reg_addr: str) -> bool:

    return True if reg_addr in register_addr.keys() else False


def ErrorCheck_A(instr_w_operand: list, idx):

    # Check for correct number of operands
    if len(instr_w_operand) != 4:
        err_gen(
            f"Type A Instructions Should Have 3 Operands Error at Line {idx+1}")

    # Check is
    if not register_addr_validation(
        instr_w_operand[1]) or not register_addr_validation(
        instr_w_operand[2]) or not register_addr_validation(
            instr_w_operand[3]):
        err_gen(f"Invalid Register Assignmnet Error at line {idx+1}")
    if 'FLAGS' in instr_w_operand:
        err_gen("Invalid Syntax ! FLAGS not allowed in Type A")


def process_A_type(instr_w_operand: list, idx) -> str:

    # Raise exception for any errors, otherwise keep runnning
    ErrorCheck_A(instr_w_operand, idx)
    machine_code.append(
        f'{opcodes[instr_w_operand[0]]}00{register_addr[instr_w_operand[1]]}{register_addr[instr_w_operand[2]]}{register_addr[instr_w_operand[3]]}'
    )


def ErrorCheck_C(instr_w_operand: list, idx):

    # Check for correct number of operands
    if len(instr_w_operand) != 3:
        err_gen(
            f"Type C Instructions Should Have 3 Operands Error at Line {idx+1}")

    # Check is
    if not register_addr_validation(
            instr_w_operand[1]) or not register_addr_validation(instr_w_operand[2]):
        err_gen(f"Invalid Register Assignmnet Error at line {idx+1}")


def process_C_type(instr_w_operand: list, idx) -> str:

    # Raise exception for any errors, otherwise keep runnning
    ErrorCheck_C(instr_w_operand, idx)
    machine_code.append(
        f'{opcodes[instr_w_operand[0]]}00000{register_addr[instr_w_operand[1]]}{register_addr[instr_w_operand[2]]}'
    )


def ErrorCheck_F(instr_w_operand: list, idx):
    if len(instr_w_operand) != 1:
        err_gen(f'HALT INSTRUCTION DOES NOT REQUIRE OPERAND {idx+1}')


def process_F_type(instr_w_operand: list, idx) -> str:

    ErrorCheck_F(instr_w_operand, idx)
    machine_code.append(f'{opcodes[instr_w_operand[0]]}' + '0' * 11)


def ErrorCheck_B(instr_w_operand: list, idx):
    if len(instr_w_operand) != 3:
        err_gen(f'TYPE B instr cannot accept more than 2 operands')

    last_operand = instr_w_operand[-1]  # Get intermediate value
    if '$' not in last_operand:
        err_gen(f'$ missing from Imm {idx+1}')
    if '$FLAGS' in instr_w_operand:
        err_gen("Invalid Syntax ! FLAGS not allowed in Type B")

    imm = int(last_operand.replace("$", ""))
    if imm >= 128 or imm < 0:
        err_gen(f'This Imm cant be represented within 7 bit {idx+1}')

    if not register_addr_validation(instr_w_operand[1]):
        err_gen(f'Invalid register {idx+1}')


def process_B_type(instr_w_operand: list, idx) -> str:

    ErrorCheck_B(instr_w_operand, idx)
    machine_code.append(
        f'{opcodes[instr_w_operand[0]]}0{register_addr[instr_w_operand[1]]}{toBin(instr_w_operand[2].replace("$",""),7)}'
    )


def ErrorCheck_D(instr_w_operand: list, idx):
    if len(instr_w_operand) != 3:
        err_gen(f'TYPE D instr cannot accept more than 3 operands {idx+1}')
    if 'FLAGS' in instr_w_operand:
        err_gen("Invalid Syntax ! FLAGS not allowed in Type D")

    # Assuming it is a variable, check it
    last_operand = instr_w_operand[-1]
    if last_operand not in var_addr_dict.keys():
        err_gen(f'Undefined varible at line {idx+1}')

    if not register_addr_validation(instr_w_operand[1]):
        err_gen(f'Undefined register at line {idx+1}')


def process_D_type(instr_w_operand: list, idx) -> str:

    ErrorCheck_D(instr_w_operand, idx)
    machine_code.append(
        f'{opcodes[instr_w_operand[0]]}0{register_addr[instr_w_operand[1]]}{var_addr_dict[instr_w_operand[2]]}'
    )


def ErrorCheck_E(instr_w_operand: list, idx):

    if len(instr_w_operand) != 2:
        err_gen(f'TYPE E instr cannot accept more than 2 operands {idx+1}')
    if 'FLAGS' in instr_w_operand:
        err_gen(f"Invalid Syntax ! FLAGS not allowed in Type E ")

    mem_addr = instr_w_operand[
        1]  # assuming its a mem address, check its a label
    if mem_addr not in label_name_dict.keys():
        err_gen(f'INVALID LABEL at line {idx+1}')


def process_E_type(instr_w_operand: list, idx) -> str:

    ErrorCheck_E(instr_w_operand, idx)
    machine_code.append(
        f'{opcodes[instr_w_operand[0]]}0000{label_name_dict[instr_w_operand[1]]}')


def process_instruction(instr_w_operand: list, idx: int):

    A_type_instr = ["add", "sub", "mul", "xor", "or", "and"]
    B_type_instr = ["rs", "ls"]
    C_type_instr = ["div", "not", "cmp"]
    D_type_instr = ["ld", "st"]
    E_type_instr = ["jmp", "jlt", "jgt", "je"]
    F_type_instr = ["hlt"]

    instr = instr_w_operand[0]
    if instr in A_type_instr:
        process_A_type(instr_w_operand, idx)
    elif instr in B_type_instr:
        process_B_type(instr_w_operand, idx)
    elif instr in C_type_instr:
        process_C_type(instr_w_operand, idx)
    elif instr in D_type_instr:
        process_D_type(instr_w_operand, idx)
    elif instr in E_type_instr:
        process_E_type(instr_w_operand, idx)
    elif instr in F_type_instr:
        process_F_type(instr_w_operand, idx)
    elif instr == "mov":
        if '$' in instr_w_operand[2]:
            instr_w_operand[0] = 'movB'  # Override with our hidden instruction
            process_B_type(instr_w_operand, idx)
        else:
            process_C_type(instr_w_operand, idx)


def process_asm(list_of_lines: str):

    for idx, line in enumerate(list_of_lines):
        instr_w_operand = line.split(' ')  # Extract first instruction
        instr_w_operand = list(filter(None, instr_w_operand))

        if len(instr_w_operand) != 0:
            instr = instr_w_operand[0]

            # If encounter a normal instruction: check and convert
            if instr in opcodes.keys():
                process_instruction(instr_w_operand, idx)

            # If we encounter a label we pass the remaining thing assuming its a instruction
            if ':' in instr and len(instr_w_operand) > 1:
                temp_instr_w_operand = instr_w_operand[1:]

                process_instruction(temp_instr_w_operand, idx)


def file_loader() -> list:
    """
          Load all lines at once, the strip the newline character ,
          then remove any  null strings from the list of lines
      """

    all_lines = []
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


def err_gen(err_str: str):

    print(err_str)
    exit()


def file_saver():

    for mc in machine_code:
        print(mc)



if __name__ == '__main__':

    list_of_lines = file_loader()

    # Assigments ki conditions check
    # Compile time check
    perform_sanity_checks(list_of_lines)

    # Conversion stage
    process_asm(list_of_lines)
    """
    """
    # print(f'\n VARS AND ITS ADDRESS\n')
    # print(var_addr_dict)

    # print(f'\n LABELS AND ITS ADDRESS\n')
    # print(label_name_dict)

    file_saver()

