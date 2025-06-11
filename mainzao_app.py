import sys
import hashlib
import getpass
import os
from datetime import datetime, date
import db_connection # Seu arquivo db_connection.py

# ------------------- UTILS ----------------------
def hash_password(password):
    """Gera o hash SHA256 de uma senha."""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_hash, provided_password):
    """Verifica se a senha fornecida corresponde ao hash armazenado."""
    return stored_hash == hash_password(provided_password)

def clear_screen():
    """Limpa a tela do terminal."""
    os.system('cls' if os.name == 'nt' else 'clear')

def press_enter_to_continue():
    """Pausa a execução até que o usuário pressione Enter."""
    input("\nPressione Enter para continuar...")

def display_menu(title, options, show_exit_option=True):
    """
    Exibe um menu formatado e obtém a escolha do usuário.

    Args:
        title (str): O título do menu.
        options (list): Uma lista de strings representando as opções do menu.
        show_exit_option (bool): Se True, adiciona "0. Voltar" ou "0. Sair".
                                 Se False, a opção 0 não é mostrada (útil para sub-menus de confirmação).
    Returns:
        int: A escolha do usuário.
    """
    print(f"\n--- {title} ---")
    for i, option in enumerate(options, 1):
        print(f"{i}. {option}")

    if show_exit_option:
        # Determina se a opção 0 deve ser "Voltar" ou "Sair"
        # Se o título contiver "Principal" ou "Login", ou se for um menu de alto nível sem "Gerenciar",
        # então "Sair" é mais apropriado. Caso contrário, "Voltar".
        if "Principal" in title or "Login" in title or "Bem-vindo" in title or not any(s in title.lower() for s in ["gerenciar", "menu d", "funções de"]):
            print("0. Sair")
        else:
            print("0. Voltar")

    while True:
        try:
            choice_str = input("Escolha uma opção: ").strip()
            if not choice_str.isdigit():
                raise ValueError("Entrada não é um número.")
            choice = int(choice_str)

            if not show_exit_option: # Se não há opção 0, valida apenas as opções > 0
                 if 1 <= choice <= len(options):
                    return choice
                 else:
                    print(f"Opção inválida. Escolha entre 1 e {len(options)}.")
            else: # Se há opção 0
                if 0 <= choice <= len(options):
                    return choice
                else:
                    print(f"Opção inválida. Escolha entre 0 e {len(options)}.")
        except ValueError:
            print("Entrada inválida. Por favor, digite um número.")

def get_valid_input(prompt, input_type=str, optional=False, choices=None):
    """
    Solicita uma entrada do usuário, valida o tipo e se é opcional.
    Se `choices` for fornecido, valida se a entrada está na lista de escolhas.
    """
    while True:
        user_input = input(prompt).strip()
        if optional and not user_input:
            return None
        if not optional and not user_input:
            print("Este campo é obrigatório.")
            continue

        try:
            if input_type == int:
                val = int(user_input)
            elif input_type == float:
                val = float(user_input)
            elif input_type == date:
                val = datetime.strptime(user_input, '%Y-%m-%d').date()
            else: # str
                val = str(user_input)

            if choices:
                if isinstance(choices, dict): # Se for um dicionário, valida contra as chaves
                    if val not in choices:
                        print(f"Opção inválida. Escolhas válidas: {', '.join(choices.keys())}")
                        continue
                elif val not in choices: # Se for uma lista
                    print(f"Opção inválida. Escolhas válidas: {', '.join(map(str,choices))}")
                    continue
            return val
        except ValueError:
            if input_type == date:
                print("Formato de data inválido. Use AAAA-MM-DD.")
            else:
                print(f"Entrada inválida. Esperado um {'número inteiro' if input_type == int else 'número decimal' if input_type == float else 'texto'}.")

# --- Lógicas de CRUD para as Entidades (Administrador) ---

# Gerenciar Pessoas (Conforme já implementado e levemente ajustado)
def manage_people_terminal(conn):
    options = ["Adicionar Pessoa", "Listar Pessoas", "Atualizar Pessoa", "Deletar Pessoa"]
    while True:
        clear_screen()
        choice = display_menu("Gerenciar Pessoas", options)

        if choice == 1: add_person_terminal(conn)
        elif choice == 2: list_people_terminal(conn)
        elif choice == 3: update_person_terminal(conn)
        elif choice == 4: delete_person_terminal(conn)
        elif choice == 0: break
        press_enter_to_continue()

def add_person_terminal(conn, return_id=False):
    print("\n--- Adicionar Nova Pessoa ---")
    name = get_valid_input("Nome: ")
    rg = get_valid_input("RG (opcional): ", optional=True)
    phone = get_valid_input("Telefone: ")
    email = get_valid_input("Email: ")

    print("\n--- Dados do Endereço ---")
    cep = get_valid_input("CEP: ")
    state = get_valid_input("Estado: ")
    city = get_valid_input("Cidade: ")
    neighborhood = get_valid_input("Bairro: ")
    street = get_valid_input("Rua: ")
    number = get_valid_input("Número: ")
    complement = get_valid_input("Complemento (opcional): ", optional=True)

    try:
        sql_insert_address = "INSERT INTO Endereco (CEP, Estado, Cidade, Bairro, Rua, Numero, Complemento) VALUES (?, ?, ?, ?, ?, ?, ?);"
        address_params = (cep, state, city, neighborhood, street, number, complement)
        new_address_id = db_connection.execute_insert_and_get_last_id(conn, sql_insert_address, address_params)

        if new_address_id is not None:
            sql_insert_person = "INSERT INTO Pessoa (Nome, RG, Telefone, Email, ID_Endereco) VALUES (?, ?, ?, ?, ?);"
            person_params = (name, rg, phone, email, new_address_id)
            
            if return_id: # Se a função foi chamada para retornar o ID da pessoa criada
                new_person_id = db_connection.execute_insert_and_get_last_id(conn, sql_insert_person, person_params)
                if new_person_id:
                    print("Pessoa e Endereço adicionados com sucesso!")
                    return new_person_id
                else:
                    print("Erro: Falha ao adicionar pessoa ou recuperar seu ID.")
                    # Rollback do endereço seria ideal aqui em um cenário transacional mais complexo
                    return None
            else: # Comportamento padrão
                result_person_insert = db_connection.execute_query(conn, sql_insert_person, person_params)
                if result_person_insert:
                    print("Pessoa e Endereço adicionados com sucesso!")
                else:
                    print("Erro: Falha ao adicionar pessoa.")
        else:
            print("Erro: Falha ao adicionar endereço ou recuperar seu ID.")
    except Exception as e:
        print(f"Erro inesperado ao adicionar pessoa: {e}")
    return None # Para o caso de return_id=False ou falha

def list_people_terminal(conn):
    print("\n--- Lista de Pessoas ---")
    sql = """
    SELECT P.Codigo_Pessoa, P.Nome, P.RG, P.Telefone, P.Email,
           E.CEP, E.Rua, E.Numero, E.Bairro, E.Cidade, E.Estado
    FROM Pessoa P
    INNER JOIN Endereco E ON P.ID_Endereco = E.ID_Endereco
    ORDER BY P.Nome;
    """
    people_data = db_connection.execute_query(conn, sql, fetch_results=True)

    if people_data:
        headers = ["Cód.", "Nome", "RG", "Telefone", "Email", "CEP", "Rua", "Nº", "Bairro", "Cidade", "UF"]
        col_widths = [5, 25, 12, 15, 25, 10, 20, 8, 15, 15, 5]
        header_format = "".join([f"{{:<{w}}}" for w in col_widths])
        print(header_format.format(*headers))
        print("-" * sum(col_widths))
        for person in people_data:
            person_formatted = [str(x) if x is not None else "" for x in person]
            print(header_format.format(*person_formatted))
    else:
        print("Nenhuma pessoa encontrada.")

def update_person_terminal(conn):
    print("\n--- Atualizar Pessoa ---")
    person_id = get_valid_input("Digite o Código Pessoa a ser atualizada: ", int)
    if person_id is None: return

    sql_get_person = """
    SELECT P.Nome, P.RG, P.Telefone, P.Email, E.ID_Endereco, E.CEP, E.Estado, E.Cidade, E.Bairro, E.Rua, E.Numero, E.Complemento
    FROM Pessoa P INNER JOIN Endereco E ON P.ID_Endereco = E.ID_Endereco
    WHERE P.Codigo_Pessoa = ?;
    """
    current_data = db_connection.execute_query(conn, sql_get_person, (person_id,), fetch_results=True)

    if not current_data:
        print("Pessoa não encontrada.")
        return

    p_data = current_data[0]
    print("\nDeixe o campo em branco para manter o valor atual.")
    new_name = input(f"Nome [{p_data[0]}]: ").strip() or p_data[0]
    new_rg = input(f"RG [{p_data[1] or ''}]: ").strip() or p_data[1]
    new_phone = input(f"Telefone [{p_data[2]}]: ").strip() or p_data[2]
    new_email = input(f"Email [{p_data[3]}]: ").strip() or p_data[3]

    address_id = p_data[4]
    new_cep = input(f"CEP [{p_data[5]}]: ").strip() or p_data[5]
    new_state = input(f"Estado [{p_data[6]}]: ").strip() or p_data[6]
    new_city = input(f"Cidade [{p_data[7]}]: ").strip() or p_data[7]
    new_neighborhood = input(f"Bairro [{p_data[8]}]: ").strip() or p_data[8]
    new_street = input(f"Rua [{p_data[9]}]: ").strip() or p_data[9]
    new_number = input(f"Número [{p_data[10]}]: ").strip() or p_data[10]
    new_complement = input(f"Complemento [{p_data[11] or ''}]: ").strip() or p_data[11]

    try:
        sql_update_address = "UPDATE Endereco SET CEP=?, Estado=?, Cidade=?, Bairro=?, Rua=?, Numero=?, Complemento=? WHERE ID_Endereco=?;"
        db_connection.execute_query(conn, sql_update_address, (new_cep, new_state, new_city, new_neighborhood, new_street, new_number, new_complement, address_id))

        sql_update_person = "UPDATE Pessoa SET Nome=?, RG=?, Telefone=?, Email=? WHERE Codigo_Pessoa=?;"
        db_connection.execute_query(conn, sql_update_person, (new_name, new_rg, new_phone, new_email, person_id))
        print("Pessoa e Endereço atualizados com sucesso!")
    except Exception as e:
        print(f"Erro inesperado ao atualizar pessoa: {e}")

def delete_person_terminal(conn):
    print("\n--- Deletar Pessoa ---")
    person_id = get_valid_input("Digite o Código Pessoa a ser deletada: ", int)
    if person_id is None: return

    # Verificar dependências antes de deletar
    # (Usuário, Cliente, Funcionário, Produto_A_Ser_Entregue como remetente/destinatário)
    dependencies = {
        "Usuario": "SELECT 1 FROM Usuario WHERE Codigo_Pessoa = ?",
        "Cliente": "SELECT 1 FROM Cliente WHERE Codigo_Pessoa = ?",
        "Funcionario": "SELECT 1 FROM Funcionario WHERE Codigo_Funcionario = ?", # Codigo_Funcionario é o mesmo que Codigo_Pessoa
        "Produto (Remetente)": "SELECT 1 FROM Produto_A_Ser_Entregue WHERE ID_Remetente = ?",
        "Produto (Destinatário)": "SELECT 1 FROM Produto_A_Ser_Entregue WHERE ID_Destinatario = ?"
    }
    for table, sql_check in dependencies.items():
        if db_connection.execute_query(conn, sql_check, (person_id,), fetch_results=True):
            print(f"Erro: Não é possível deletar. Pessoa está referenciada na tabela {table}.")
            return

    # Obter ID_Endereco para deletar o endereço também
    address_id_data = db_connection.execute_query(conn, "SELECT ID_Endereco FROM Pessoa WHERE Codigo_Pessoa = ?", (person_id,), fetch_results=True)
    
    confirm = input(f"Tem certeza que deseja deletar a pessoa com Cód. {person_id} e seu endereço? (s/n): ").strip().lower()
    if confirm != 's':
        print("Exclusão cancelada.")
        return

    try:
        # Deletar Pessoa (ON DELETE CASCADE cuidaria disso no DB se configurado, mas fazemos manualmente)
        if db_connection.execute_query(conn, "DELETE FROM Pessoa WHERE Codigo_Pessoa = ?", (person_id,)):
            print("Pessoa deletada.")
            if address_id_data:
                address_id = address_id_data[0][0]
                # Verificar se o endereço é usado por outra Pessoa ou Sede antes de deletar
                sql_check_addr_pessoa = "SELECT 1 FROM Pessoa WHERE ID_Endereco = ? AND Codigo_Pessoa != ?" # Exclui a pessoa que acabamos de deletar
                sql_check_addr_sede = "SELECT 1 FROM Sede WHERE ID_Endereco = ?"
                if not db_connection.execute_query(conn, sql_check_addr_pessoa, (address_id, person_id), fetch_results=True) and \
                   not db_connection.execute_query(conn, sql_check_addr_sede, (address_id,), fetch_results=True):
                    if db_connection.execute_query(conn, "DELETE FROM Endereco WHERE ID_Endereco = ?", (address_id,)):
                        print("Endereço associado deletado com sucesso.")
                    else:
                        print("Aviso: Pessoa deletada, mas falha ao deletar endereço (pode ainda estar em uso ou erro).")
                else:
                    print("Aviso: Pessoa deletada, mas o endereço não foi removido pois está em uso por outra entidade.")
            else:
                print("Aviso: Pessoa deletada, mas não foi possível encontrar/deletar o endereço associado.")
        else:
            print("Erro: Falha ao deletar pessoa.")
    except Exception as e:
        print(f"Erro inesperado ao deletar pessoa: {e}")

# Gerenciar Usuários (Conforme já implementado e levemente ajustado)
def manage_users_terminal(conn):
    options = ["Adicionar Usuário", "Listar Usuários", "Atualizar Usuário", "Deletar Usuário"]
    while True:
        clear_screen()
        choice = display_menu("Gerenciar Usuários", options)
        if choice == 1: add_user_terminal(conn)
        elif choice == 2: list_users_terminal(conn)
        elif choice == 3: update_user_terminal(conn)
        elif choice == 4: delete_user_terminal(conn)
        elif choice == 0: break
        press_enter_to_continue()

def add_user_terminal(conn):
    print("\n--- Adicionar Novo Usuário ---")
    login = get_valid_input("Login: ")
    password = getpass.getpass("Senha: ").strip()
    while not password:
        print("Senha não pode ser vazia.")
        password = getpass.getpass("Senha: ").strip()

    person_code = get_valid_input("Código Pessoa (de uma pessoa já cadastrada): ", int)
    if person_code is None: return

    # Verificar se Codigo_Pessoa existe
    if not db_connection.execute_query(conn, "SELECT 1 FROM Pessoa WHERE Codigo_Pessoa = ?", (person_code,), fetch_results=True):
        print("Erro: Código Pessoa não encontrado. Cadastre a pessoa primeiro.")
        return

    # Verificar se já existe um usuário para este Codigo_Pessoa
    if db_connection.execute_query(conn, "SELECT 1 FROM Usuario WHERE Codigo_Pessoa = ?", (person_code,), fetch_results=True):
        print("Erro: Já existe um usuário associado a este Código Pessoa.")
        return

    valid_user_types = ['Cliente', 'Motorista', 'Auxiliar de Logistica', 'Atendente', 'Gerente', 'Admin']
    user_type = get_valid_input(f"Tipo de Usuário ({', '.join(valid_user_types)}): ", choices=valid_user_types)
    if user_type is None: return

    # Lógica para garantir consistência com tabelas Cliente/Funcionario
    if user_type == 'Cliente':
        if not db_connection.execute_query(conn, "SELECT 1 FROM Cliente WHERE Codigo_Pessoa = ?", (person_code,), fetch_results=True):
            print(f"Atenção: Esta pessoa (Cód: {person_code}) não está cadastrada como Cliente.")
            if input("Deseja cadastrá-la como Cliente agora? (s/n): ").lower() == 's':
                # Simplificado: Chamar uma função para adicionar apenas o registro em Cliente
                # Supondo que a pessoa já tem os dados necessários (PF/PJ) para serem preenchidos.
                # Para um sistema real, seria preciso coletar esses dados aqui.
                # Por ora, vamos assumir que o admin fará isso via "Gerenciar Clientes".
                print("Por favor, cadastre esta pessoa como Cliente através do menu 'Gerenciar Clientes' antes de criar o usuário Cliente.")
                return
            else:
                print("Criação de usuário cancelada. Pessoa não é um Cliente.")
                return
    elif user_type in ['Motorista', 'Auxiliar de Logistica', 'Atendente', 'Gerente', 'Admin']:
        if not db_connection.execute_query(conn, "SELECT 1 FROM Funcionario WHERE Codigo_Funcionario = ?", (person_code,), fetch_results=True):
            print(f"Atenção: Esta pessoa (Cód: {person_code}) não está cadastrada como Funcionário.")
            if input("Deseja cadastrá-la como Funcionário agora? (s/n): ").lower() == 's':
                print("Por favor, cadastre esta pessoa como Funcionário através do menu 'Gerenciar Funcionários' antes de criar o usuário funcionário.")
                return
            else:
                print("Criação de usuário cancelada. Pessoa não é um Funcionário.")
                return
        # Adicionalmente, verificar se o Cargo do funcionário corresponde ao Tipo_Usuario
        func_data = db_connection.execute_query(conn, "SELECT Cargo FROM Funcionario WHERE Codigo_Funcionario = ?", (person_code,), fetch_results=True)
        if func_data and func_data[0][0].replace(" ", "") != user_type.replace(" ", ""): # Compara ignorando espaços
            if not (func_data[0][0] == 'Gerente' and user_type == 'Admin'): # Permitir que um Gerente seja Admin
                 print(f"Aviso: O cargo do funcionário ({func_data[0][0]}) não corresponde exatamente ao tipo de usuário ({user_type}).")
                 if input("Continuar mesmo assim? (s/n): ").lower() != 's':
                     return


    hashed_password = hash_password(password)
    sql = "INSERT INTO Usuario (Login, Senha_Hash, Codigo_Pessoa, Tipo_Usuario) VALUES (?, ?, ?, ?)"
    if db_connection.execute_query(conn, sql, (login, hashed_password, person_code, user_type)):
        print("Usuário adicionado com sucesso!")
    else:
        print("Erro: Falha ao adicionar usuário. O login pode já existir.")

def list_users_terminal(conn):
    print("\n--- Lista de Usuários ---")
    sql = "SELECT U.Login, U.Codigo_Pessoa, P.Nome, U.Tipo_Usuario FROM Usuario U JOIN Pessoa P ON U.Codigo_Pessoa = P.Codigo_Pessoa ORDER BY U.Login"
    users = db_connection.execute_query(conn, sql, fetch_results=True)
    if users:
        headers = ["Login", "Cód. Pessoa", "Nome Pessoa", "Tipo Usuário"]
        col_widths = [20, 12, 30, 25]
        header_format = "".join([f"{{:<{w}}}" for w in col_widths])
        print(header_format.format(*headers))
        print("-" * sum(col_widths))
        for user in users:
            print(header_format.format(*user))
    else:
        print("Nenhum usuário encontrado.")

def update_user_terminal(conn):
    print("\n--- Atualizar Usuário ---")
    login_to_update = get_valid_input("Digite o Login do usuário a ser atualizado: ")
    if login_to_update is None: return

    user_data = db_connection.execute_query(conn, "SELECT Senha_Hash, Codigo_Pessoa, Tipo_Usuario FROM Usuario WHERE Login = ?", (login_to_update,), fetch_results=True)
    if not user_data:
        print("Usuário não encontrado.")
        return

    _, current_person_code, current_user_type = user_data[0]

    print(f"\nAtualizando usuário: {login_to_update}")
    print(f"Código Pessoa atual: {current_person_code}, Tipo atual: {current_user_type}")
    print("Deixe em branco para manter o valor atual.")

    new_password = getpass.getpass("Nova Senha (deixe em branco para não alterar): ").strip()
    
    # Não permitir alterar Codigo_Pessoa ou Tipo_Usuario diretamente aqui para simplificar.
    # Se necessário, o admin deve deletar e recriar o usuário com os novos vínculos.
    # Ou implementar uma lógica mais complexa de validação de mudança de tipo/pessoa.
    print(f"Código Pessoa ({current_person_code}) e Tipo de Usuário ({current_user_type}) não podem ser alterados diretamente.")
    print("Para alterar o tipo ou a pessoa associada, delete e recrie o usuário.")


    if new_password:
        hashed_password = hash_password(new_password)
        sql = "UPDATE Usuario SET Senha_Hash = ? WHERE Login = ?"
        params = (hashed_password, login_to_update)
    else: # Nenhuma alteração se apenas a senha não foi mudada
        print("Nenhuma alteração na senha. Nada a atualizar.")
        return

    if db_connection.execute_query(conn, sql, params):
        print("Usuário atualizado com sucesso!")
    else:
        print("Erro: Falha ao atualizar usuário.")

def delete_user_terminal(conn):
    print("\n--- Deletar Usuário ---")
    login_to_delete = get_valid_input("Digite o Login do usuário a ser deletado: ")
    if login_to_delete is None: return

    if not db_connection.execute_query(conn, "SELECT 1 FROM Usuario WHERE Login = ?", (login_to_delete,), fetch_results=True):
        print("Usuário não encontrado.")
        return

    confirm = input(f"Tem certeza que deseja deletar o usuário '{login_to_delete}'? (s/n): ").strip().lower()
    if confirm != 's':
        print("Exclusão cancelada.")
        return

    if db_connection.execute_query(conn, "DELETE FROM Usuario WHERE Login = ?", (login_to_delete,)):
        print("Usuário deletado com sucesso!")
    else:
        print("Erro: Falha ao deletar usuário.")

# Gerenciar Clientes (Conforme já implementado e levemente ajustado)
def manage_clients_terminal(conn):
    options = ["Adicionar Cliente", "Listar Clientes", "Atualizar Cliente", "Deletar Cliente"]
    while True:
        clear_screen()
        choice = display_menu("Gerenciar Clientes", options)
        if choice == 1: add_client_terminal(conn)
        elif choice == 2: list_clients_terminal(conn)
        elif choice == 3: update_client_terminal(conn)
        elif choice == 4: delete_client_terminal(conn)
        elif choice == 0: break
        press_enter_to_continue()

def add_client_terminal(conn, person_code_param=None, client_type_param=None, cpf_param=None, dob_param=None, cnpj_param=None, company_name_param=None):
    print("\n--- Adicionar Novo Cliente ---")
    if person_code_param is None:
        person_code = get_valid_input("Código Pessoa (de uma pessoa já cadastrada): ", int)
        if person_code is None: return
    else:
        person_code = person_code_param

    if not db_connection.execute_query(conn, "SELECT 1 FROM Pessoa WHERE Codigo_Pessoa = ?", (person_code,), fetch_results=True):
        print("Erro: Código Pessoa não encontrado. Cadastre a pessoa primeiro.")
        return
    if db_connection.execute_query(conn, "SELECT 1 FROM Cliente WHERE Codigo_Pessoa = ?", (person_code,), fetch_results=True):
        print("Erro: Já existe um cliente associado a este Código Pessoa.")
        return

    if client_type_param is None:
        client_type = get_valid_input("Tipo de Cliente (PF - Pessoa Física / PJ - Pessoa Jurídica): ", str.upper, choices=['PF', 'PJ'])
        if client_type is None: return
    else:
        client_type = client_type_param

    cpf, dob, cnpj, company_name = None, None, None, None
    if client_type == 'PF':
        cpf = cpf_param if cpf_param else get_valid_input("CPF: ")
        dob_str = dob_param if dob_param else get_valid_input("Data de Nascimento (AAAA-MM-DD): ", str) # Pegar como string primeiro
        try:
            dob = datetime.strptime(dob_str, '%Y-%m-%d').date() if isinstance(dob_str, str) else dob_str
        except ValueError:
            print("Erro: Formato de data inválido. Use AAAA-MM-DD.")
            return
    elif client_type == 'PJ':
        cnpj = cnpj_param if cnpj_param else get_valid_input("CNPJ: ")
        company_name = company_name_param if company_name_param else get_valid_input("Nome da Empresa: ")

    sql = "INSERT INTO Cliente (Codigo_Pessoa, Tipo_Cliente, CPF, Data_Nascimento, CNPJ, Nome_Empresa) VALUES (?, ?, ?, ?, ?, ?);"
    if db_connection.execute_query(conn, sql, (person_code, client_type, cpf, dob, cnpj, company_name)):
        print("Cliente adicionado com sucesso!")
        return True
    else:
        print("Erro: Falha ao adicionar cliente. Verifique os dados e as constraints da tabela (CHK_Cliente_PF_PJ).")
        return False

def list_clients_terminal(conn):
    print("\n--- Lista de Clientes ---")
    sql = """
    SELECT C.Codigo_Pessoa, P.Nome, C.Tipo_Cliente, C.CPF, 
           FORMAT(C.Data_Nascimento, 'dd/MM/yyyy') AS Data_Nascimento, 
           C.CNPJ, C.Nome_Empresa
    FROM Cliente C
    INNER JOIN Pessoa P ON C.Codigo_Pessoa = P.Codigo_Pessoa
    ORDER BY P.Nome;
    """
    clients_data = db_connection.execute_query(conn, sql, fetch_results=True)
    if clients_data:
        headers = ["Cód. Pessoa", "Nome", "Tipo", "CPF", "Data Nasc.", "CNPJ", "Nome Empresa"]
        col_widths = [12, 25, 8, 15, 12, 20, 30]
        header_format = "".join([f"{{:<{w}}}" for w in col_widths])
        print(header_format.format(*headers))
        print("-" * sum(col_widths))
        for client in clients_data:
            client_formatted = [str(x) if x is not None else "" for x in client]
            print(header_format.format(*client_formatted))
    else:
        print("Nenhum cliente encontrado.")

def update_client_terminal(conn, person_code_logged_in=None):
    print("\n--- Atualizar Cliente ---")
    if person_code_logged_in:
        person_code = person_code_logged_in
        print(f"Atualizando seus dados de cliente (Código Pessoa: {person_code}).")
    else:
        person_code = get_valid_input("Digite o Código Pessoa do cliente a ser atualizado: ", int)
        if person_code is None: return

    sql_get_client = """
    SELECT P.Nome, C.Tipo_Cliente, C.CPF, C.Data_Nascimento, C.CNPJ, C.Nome_Empresa
    FROM Cliente C INNER JOIN Pessoa P ON C.Codigo_Pessoa = P.Codigo_Pessoa
    WHERE C.Codigo_Pessoa = ?;
    """
    current_data = db_connection.execute_query(conn, sql_get_client, (person_code,), fetch_results=True)
    if not current_data:
        print("Cliente não encontrado.")
        return

    c_data = current_data[0]
    print(f"\nNome da Pessoa associada: {c_data[0]}")
    print("Deixe o campo em branco para manter o valor atual.")

    new_client_type = input(f"Tipo de Cliente [{c_data[1]}] (PF/PJ): ").strip().upper() or c_data[1]
    if new_client_type not in ['PF', 'PJ']:
        print("Erro: Tipo de cliente inválido. Mantendo o anterior.")
        new_client_type = c_data[1]

    new_cpf, new_dob, new_cnpj, new_company_name = c_data[2], c_data[3], c_data[4], c_data[5]

    if new_client_type == 'PF':
        new_cpf = input(f"CPF [{c_data[2] or ''}]: ").strip() or c_data[2]
        dob_str = input(f"Data de Nascimento [{c_data[3] or ''}] (AAAA-MM-DD): ").strip()
        if dob_str:
            try:
                new_dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
            except ValueError:
                print("Formato de data inválido. Mantendo data anterior.")
        new_cnpj, new_company_name = None, None
    elif new_client_type == 'PJ':
        new_cnpj = input(f"CNPJ [{c_data[4] or ''}]: ").strip() or c_data[4]
        new_company_name = input(f"Nome da Empresa [{c_data[5] or ''}]: ").strip() or c_data[5]
        new_cpf, new_dob = None, None

    sql_update = "UPDATE Cliente SET Tipo_Cliente=?, CPF=?, Data_Nascimento=?, CNPJ=?, Nome_Empresa=? WHERE Codigo_Pessoa=?;"
    if db_connection.execute_query(conn, sql_update, (new_client_type, new_cpf, new_dob, new_cnpj, new_company_name, person_code)):
        print("Cliente atualizado com sucesso!")
    else:
        print("Erro: Falha ao atualizar cliente. Verifique os dados e as constraints (CHK_Cliente_PF_PJ).")

def delete_client_terminal(conn):
    print("\n--- Deletar Cliente ---")
    person_code = get_valid_input("Digite o Código Pessoa do cliente a ser deletado: ", int)
    if person_code is None: return

    # Verificar dependências (Produto_A_Ser_Entregue, Usuario)
    if db_connection.execute_query(conn, "SELECT 1 FROM Produto_A_Ser_Entregue WHERE ID_Remetente = ? OR ID_Destinatario = ?", (person_code, person_code), fetch_results=True):
        print("Erro: Cliente está associado a produtos. Não pode ser deletado.")
        return
    if db_connection.execute_query(conn, "SELECT 1 FROM Usuario WHERE Codigo_Pessoa = ? AND Tipo_Usuario = 'Cliente'", (person_code,), fetch_results=True):
        print("Erro: Cliente possui um usuário associado. Delete o usuário primeiro ou altere seu tipo.")
        return
    
    client_name_data = db_connection.execute_query(conn, "SELECT P.Nome FROM Cliente C INNER JOIN Pessoa P ON C.Codigo_Pessoa = P.Codigo_Pessoa WHERE C.Codigo_Pessoa = ?", (person_code,), fetch_results=True)
    client_name = client_name_data[0][0] if client_name_data else f"Cód: {person_code}"


    confirm = input(f"Tem certeza que deseja deletar o cliente '{client_name}'? (s/n): ").strip().lower()
    if confirm != 's':
        print("Exclusão cancelada.")
        return

    if db_connection.execute_query(conn, "DELETE FROM Cliente WHERE Codigo_Pessoa = ?", (person_code,)):
        print(f"Cliente '{client_name}' deletado com sucesso!")
        print("Lembre-se: A Pessoa associada e seu Endereço NÃO foram deletados. Use 'Gerenciar Pessoas' para isso, se necessário.")
    else:
        print("Erro: Falha ao deletar cliente.")


# --- Gerenciar Funcionários ---
def manage_employees_terminal(conn):
    options = ["Adicionar Funcionário", "Listar Funcionários", "Atualizar Funcionário", "Deletar Funcionário"]
    while True:
        clear_screen()
        choice = display_menu("Gerenciar Funcionários", options)
        if choice == 1: add_employee_terminal(conn)
        elif choice == 2: list_employees_terminal(conn)
        elif choice == 3: update_employee_terminal(conn)
        elif choice == 4: delete_employee_terminal(conn)
        elif choice == 0: break
        press_enter_to_continue()

def add_employee_terminal(conn):
    print("\n--- Adicionar Novo Funcionário ---")
    person_code = get_valid_input("Código Pessoa (de uma pessoa já cadastrada para ser funcionário): ", int)
    if person_code is None: return

    if not db_connection.execute_query(conn, "SELECT 1 FROM Pessoa WHERE Codigo_Pessoa = ?", (person_code,), fetch_results=True):
        print("Erro: Código Pessoa não encontrado. Cadastre a pessoa primeiro.")
        return
    if db_connection.execute_query(conn, "SELECT 1 FROM Funcionario WHERE Codigo_Funcionario = ?", (person_code,), fetch_results=True):
        print("Erro: Esta pessoa já está cadastrada como funcionário.")
        return

    cpf = get_valid_input("CPF do Funcionário: ")
    # Verificar se CPF já existe para outro funcionário
    if db_connection.execute_query(conn, "SELECT 1 FROM Funcionario WHERE CPF = ? AND Codigo_Funcionario != ?", (cpf, person_code), fetch_results=True):
        print("Erro: Este CPF já está cadastrado para outro funcionário.")
        return
    
    departamento = get_valid_input("Departamento (ex: Entregas, Atendimento, Administrativo): ")
    
    cargos_validos = ['Motorista', 'Auxiliar de Logistica', 'Atendente', 'Gerente', 'Admin']
    cargo = get_valid_input(f"Cargo ({', '.join(cargos_validos)}): ", choices=cargos_validos)
    if cargo is None: return

    placa_veiculo, id_sede = None, None
    if cargo == 'Motorista':
        list_available_vehicles(conn) # Mostrar veículos disponíveis
        placa_veiculo = get_valid_input("Placa do Veículo (de um veículo existente e disponível): ")
        # Validar se a placa existe e está disponível
        vehicle_data = db_connection.execute_query(conn, "SELECT Status FROM Veiculo WHERE Placa_Veiculo = ?", (placa_veiculo,), fetch_results=True)
        if not vehicle_data:
            print("Erro: Veículo não encontrado.")
            return
        # if vehicle_data[0][0] == 'Indisponivel':
        #     print("Erro: Veículo está indisponível.") # Motorista pode ser associado a um veículo mesmo que temporariamente indisponível. Status do veículo é gerenciado à parte.
        #     return
    elif cargo in ['Auxiliar de Logistica', 'Atendente', 'Gerente']:
        list_headquarters_terminal(conn, simple_list=True) # Mostrar sedes
        id_sede = get_valid_input("ID da Sede: ", int)
        if not db_connection.execute_query(conn, "SELECT 1 FROM Sede WHERE ID_Sede = ?", (id_sede,), fetch_results=True):
            print("Erro: Sede não encontrada.")
            return
    # Admin não requer placa nem sede por padrão na constraint, mas pode ser atribuído a uma sede se desejado (não implementado aqui)

    sql = """
    INSERT INTO Funcionario (Codigo_Funcionario, CPF, Departamento, Cargo, Placa_Veiculo, ID_Sede)
    VALUES (?, ?, ?, ?, ?, ?);
    """
    params = (person_code, cpf, departamento, cargo, placa_veiculo, id_sede)
    if db_connection.execute_query(conn, sql, params):
        print("Funcionário adicionado com sucesso!")
    else:
        print("Erro: Falha ao adicionar funcionário. Verifique os dados e as constraints (CHK_Funcionario_Cargo).")

def list_employees_terminal(conn):
    print("\n--- Lista de Funcionários ---")
    sql = """
    SELECT F.Codigo_Funcionario, P.Nome, F.CPF, F.Departamento, F.Cargo, 
           F.Placa_Veiculo, F.ID_Sede, S.Tipo AS Tipo_Sede, E.Cidade AS Cidade_Sede
    FROM Funcionario F
    INNER JOIN Pessoa P ON F.Codigo_Funcionario = P.Codigo_Pessoa
    LEFT JOIN Sede S ON F.ID_Sede = S.ID_Sede
    LEFT JOIN Endereco E ON S.ID_Endereco = E.ID_Endereco
    ORDER BY P.Nome;
    """
    employees = db_connection.execute_query(conn, sql, fetch_results=True)
    if employees:
        headers = ["Cód. Func", "Nome", "CPF", "Depto", "Cargo", "Placa Veíc.", "ID Sede", "Tipo Sede", "Cidade Sede"]
        col_widths = [10, 25, 15, 20, 20, 12, 8, 10, 15]
        header_format = "".join([f"{{:<{w}}}" for w in col_widths])
        print(header_format.format(*headers))
        print("-" * sum(col_widths))
        for emp in employees:
            emp_formatted = [str(x) if x is not None else "" for x in emp]
            print(header_format.format(*emp_formatted))
    else:
        print("Nenhum funcionário encontrado.")

def update_employee_terminal(conn):
    print("\n--- Atualizar Funcionário ---")
    person_code = get_valid_input("Digite o Código do Funcionário (que é o Código Pessoa) a ser atualizado: ", int)
    if person_code is None: return

    sql_get_emp = """
    SELECT P.Nome, F.CPF, F.Departamento, F.Cargo, F.Placa_Veiculo, F.ID_Sede
    FROM Funcionario F INNER JOIN Pessoa P ON F.Codigo_Funcionario = P.Codigo_Pessoa
    WHERE F.Codigo_Funcionario = ?;
    """
    current_data = db_connection.execute_query(conn, sql_get_emp, (person_code,), fetch_results=True)
    if not current_data:
        print("Funcionário não encontrado.")
        return

    e_data = current_data[0]
    print(f"\nAtualizando funcionário: {e_data[0]} (Cód: {person_code})")
    print("Deixe em branco para manter o valor atual.")

    new_cpf = input(f"CPF [{e_data[1]}]: ").strip() or e_data[1]
    if new_cpf != e_data[1] and db_connection.execute_query(conn, "SELECT 1 FROM Funcionario WHERE CPF = ? AND Codigo_Funcionario != ?", (new_cpf, person_code), fetch_results=True):
        print("Erro: Este CPF já está cadastrado para outro funcionário. Mantendo CPF anterior.")
        new_cpf = e_data[1]
        
    new_departamento = input(f"Departamento [{e_data[2]}]: ").strip() or e_data[2]
    
    cargos_validos = ['Motorista', 'Auxiliar de Logistica', 'Atendente', 'Gerente', 'Admin']
    new_cargo = input(f"Cargo [{e_data[3]}] ({', '.join(cargos_validos)}): ").strip() or e_data[3]
    if new_cargo not in cargos_validos:
        print("Cargo inválido. Mantendo cargo anterior.")
        new_cargo = e_data[3]

    new_placa_veiculo, new_id_sede = e_data[4], e_data[5]
    if new_cargo == 'Motorista':
        list_available_vehicles(conn)
        new_placa_veiculo_input = input(f"Placa do Veículo [{e_data[4] or ''}]: ").strip()
        if new_placa_veiculo_input: # Só atualiza se algo for digitado
            if db_connection.execute_query(conn, "SELECT 1 FROM Veiculo WHERE Placa_Veiculo = ?", (new_placa_veiculo_input,), fetch_results=True):
                new_placa_veiculo = new_placa_veiculo_input
            else:
                print("Placa de veículo inválida. Mantendo anterior (ou nenhuma).")
        new_id_sede = None # Motorista não tem sede diretamente na tabela Funcionario
    elif new_cargo in ['Auxiliar de Logistica', 'Atendente', 'Gerente']:
        list_headquarters_terminal(conn, simple_list=True)
        new_id_sede_input = input(f"ID da Sede [{e_data[5] or ''}]: ").strip()
        if new_id_sede_input:
            try:
                new_id_sede_val = int(new_id_sede_input)
                if db_connection.execute_query(conn, "SELECT 1 FROM Sede WHERE ID_Sede = ?", (new_id_sede_val,), fetch_results=True):
                    new_id_sede = new_id_sede_val
                else:
                    print("ID de sede inválido. Mantendo anterior (ou nenhuma).")
            except ValueError:
                print("ID de sede deve ser um número. Mantendo anterior (ou nenhuma).")
        new_placa_veiculo = None # Outros cargos não têm placa
    else: # Admin, etc.
        new_placa_veiculo, new_id_sede = None, None


    sql_update = "UPDATE Funcionario SET CPF=?, Departamento=?, Cargo=?, Placa_Veiculo=?, ID_Sede=? WHERE Codigo_Funcionario=?;"
    params = (new_cpf, new_departamento, new_cargo, new_placa_veiculo, new_id_sede, person_code)
    if db_connection.execute_query(conn, sql_update, params):
        print("Funcionário atualizado com sucesso!")
    else:
        print("Erro: Falha ao atualizar funcionário. Verifique os dados e as constraints (CHK_Funcionario_Cargo).")

def delete_employee_terminal(conn):
    print("\n--- Deletar Funcionário ---")
    person_code = get_valid_input("Digite o Código do Funcionário (Pessoa) a ser deletado: ", int)
    if person_code is None: return

    # Verificar dependências (Produto_A_Ser_Entregue como motorista, Usuario)
    if db_connection.execute_query(conn, "SELECT 1 FROM Produto_A_Ser_Entregue WHERE Codigo_Funcionario_Motorista = ?", (person_code,), fetch_results=True):
        print("Erro: Funcionário é motorista de produtos. Não pode ser deletado.")
        return
    if db_connection.execute_query(conn, "SELECT 1 FROM Usuario WHERE Codigo_Pessoa = ? AND Tipo_Usuario != 'Cliente'", (person_code,), fetch_results=True):
        print("Erro: Funcionário possui um usuário associado. Delete o usuário primeiro ou altere seu tipo.")
        return
        
    emp_name_data = db_connection.execute_query(conn, "SELECT P.Nome FROM Funcionario F INNER JOIN Pessoa P ON F.Codigo_Funcionario = P.Codigo_Pessoa WHERE F.Codigo_Funcionario = ?", (person_code,), fetch_results=True)
    emp_name = emp_name_data[0][0] if emp_name_data else f"Cód: {person_code}"

    confirm = input(f"Tem certeza que deseja deletar o funcionário '{emp_name}'? (s/n): ").strip().lower()
    if confirm != 's':
        print("Exclusão cancelada.")
        return

    if db_connection.execute_query(conn, "DELETE FROM Funcionario WHERE Codigo_Funcionario = ?", (person_code,)):
        print(f"Funcionário '{emp_name}' deletado com sucesso!")
        print("Lembre-se: A Pessoa associada e seu Endereço NÃO foram deletados. Use 'Gerenciar Pessoas' para isso, se necessário.")
    else:
        print("Erro: Falha ao deletar funcionário.")

# --- Gerenciar Veículos ---
def manage_vehicles_terminal(conn):
    options = ["Adicionar Veículo", "Listar Veículos", "Atualizar Veículo", "Deletar Veículo"]
    while True:
        clear_screen()
        choice = display_menu("Gerenciar Veículos", options)
        if choice == 1: add_vehicle_terminal(conn)
        elif choice == 2: list_vehicles_terminal(conn)
        elif choice == 3: update_vehicle_terminal(conn)
        elif choice == 4: delete_vehicle_terminal(conn)
        elif choice == 0: break
        press_enter_to_continue()

def add_vehicle_terminal(conn):
    print("\n--- Adicionar Novo Veículo ---")
    placa = get_valid_input("Placa do Veículo: ", str.upper)
    if db_connection.execute_query(conn, "SELECT 1 FROM Veiculo WHERE Placa_Veiculo = ?", (placa,), fetch_results=True):
        print("Erro: Veículo com esta placa já cadastrado.")
        return
    
    carga_suportada = get_valid_input("Carga Suportada (kg): ", float)
    tipos_validos = ['Carro', 'Moto', 'Van', 'Caminhão']
    tipo = get_valid_input(f"Tipo ({', '.join(tipos_validos)}): ", choices=tipos_validos)
    status_validos = ['Disponivel', 'Indisponivel'] # 'Em Manutenção', 'Em Rota' poderiam ser outros status
    status = get_valid_input(f"Status Inicial ({', '.join(status_validos)}): ", choices=status_validos)

    sql = "INSERT INTO Veiculo (Placa_Veiculo, Carga_Suportada, Tipo, Status) VALUES (?, ?, ?, ?);"
    if db_connection.execute_query(conn, sql, (placa, carga_suportada, tipo, status)):
        print("Veículo adicionado com sucesso!")
    else:
        print("Erro: Falha ao adicionar veículo.")

def list_available_vehicles(conn):
    """Lista veículos disponíveis para atribuição a motoristas ou carregamentos."""
    print("\n--- Veículos Disponíveis ---")
    sql = "SELECT Placa_Veiculo, Tipo, Carga_Suportada FROM Veiculo WHERE Status = 'Disponivel' ORDER BY Placa_Veiculo;"
    vehicles = db_connection.execute_query(conn, sql, fetch_results=True)
    if vehicles:
        headers = ["Placa", "Tipo", "Carga (kg)"]
        col_widths = [10, 15, 10]
        header_format = "".join([f"{{:<{w}}}" for w in col_widths])
        print(header_format.format(*headers))
        print("-" * sum(col_widths))
        for v in vehicles:
            print(header_format.format(*v))
    else:
        print("Nenhum veículo disponível encontrado.")

def list_vehicles_terminal(conn):
    print("\n--- Lista de Veículos ---")
    sql = "SELECT Placa_Veiculo, Carga_Suportada, Tipo, Status FROM Veiculo ORDER BY Placa_Veiculo;"
    vehicles = db_connection.execute_query(conn, sql, fetch_results=True)
    if vehicles:
        headers = ["Placa", "Carga (kg)", "Tipo", "Status"]
        col_widths = [10, 12, 15, 15]
        header_format = "".join([f"{{:<{w}}}" for w in col_widths])
        print(header_format.format(*headers))
        print("-" * sum(col_widths))
        for v in vehicles:
            v_formatted = [str(x) if x is not None else "" for x in v]
            print(header_format.format(*v_formatted))
    else:
        print("Nenhum veículo encontrado.")

def update_vehicle_terminal(conn):
    print("\n--- Atualizar Veículo ---")
    placa = get_valid_input("Digite a Placa do veículo a ser atualizado: ", str.upper)
    if placa is None: return

    current_data = db_connection.execute_query(conn, "SELECT Carga_Suportada, Tipo, Status FROM Veiculo WHERE Placa_Veiculo = ?", (placa,), fetch_results=True)
    if not current_data:
        print("Veículo não encontrado.")
        return
    
    v_data = current_data[0]
    print(f"Atualizando veículo: {placa}")
    print("Deixe em branco para manter o valor atual.")

    new_carga = input(f"Carga Suportada (kg) [{v_data[0]}]: ").strip()
    new_carga = float(new_carga) if new_carga else v_data[0]

    tipos_validos = ['Carro', 'Moto', 'Van', 'Caminhão']
    new_tipo = input(f"Tipo [{v_data[1]}] ({', '.join(tipos_validos)}): ").strip() or v_data[1]
    if new_tipo not in tipos_validos:
        print("Tipo inválido. Mantendo anterior.")
        new_tipo = v_data[1]

    status_validos = ['Disponivel', 'Indisponivel']
    new_status = input(f"Status [{v_data[2]}] ({', '.join(status_validos)}): ").strip() or v_data[2]
    if new_status not in status_validos:
        print("Status inválido. Mantendo anterior.")
        new_status = v_data[2]

    sql = "UPDATE Veiculo SET Carga_Suportada=?, Tipo=?, Status=? WHERE Placa_Veiculo=?;"
    if db_connection.execute_query(conn, sql, (new_carga, new_tipo, new_status, placa)):
        print("Veículo atualizado com sucesso!")
    else:
        print("Erro: Falha ao atualizar veículo.")

def delete_vehicle_terminal(conn):
    print("\n--- Deletar Veículo ---")
    placa = get_valid_input("Digite a Placa do veículo a ser deletado: ", str.upper)
    if placa is None: return

    # Verificar dependências (Funcionario, Carregamento)
    if db_connection.execute_query(conn, "SELECT 1 FROM Funcionario WHERE Placa_Veiculo = ?", (placa,), fetch_results=True):
        print("Erro: Veículo está associado a um funcionário (Motorista). Desvincule-o primeiro.")
        return
    if db_connection.execute_query(conn, "SELECT 1 FROM Carregamento WHERE Placa_Veiculo = ?", (placa,), fetch_results=True):
        print("Erro: Veículo possui carregamentos associados. Não pode ser deletado.")
        return

    if not db_connection.execute_query(conn, "SELECT 1 FROM Veiculo WHERE Placa_Veiculo = ?", (placa,), fetch_results=True):
        print("Veículo não encontrado.")
        return

    confirm = input(f"Tem certeza que deseja deletar o veículo de placa '{placa}'? (s/n): ").strip().lower()
    if confirm != 's':
        print("Exclusão cancelada.")
        return

    if db_connection.execute_query(conn, "DELETE FROM Veiculo WHERE Placa_Veiculo = ?", (placa,)):
        print("Veículo deletado com sucesso!")
    else:
        print("Erro: Falha ao deletar veículo.")

# --- Gerenciar Sedes ---
def manage_headquarters_terminal(conn):
    options = ["Adicionar Sede", "Listar Sedes", "Atualizar Sede", "Deletar Sede"]
    while True:
        clear_screen()
        choice = display_menu("Gerenciar Sedes", options)
        if choice == 1: add_headquarters_terminal(conn)
        elif choice == 2: list_headquarters_terminal(conn)
        elif choice == 3: update_headquarters_terminal(conn)
        elif choice == 4: delete_headquarters_terminal(conn)
        elif choice == 0: break
        press_enter_to_continue()

def add_headquarters_terminal(conn):
    print("\n--- Adicionar Nova Sede ---")
    tipos_sede = {1: "Distribuição", 2: "Loja", 3: "Ambos"}
    print("Tipos de Sede:")
    for k,v in tipos_sede.items(): print(f"  {k} - {v}")
    tipo_id = get_valid_input("Tipo da Sede (ID): ", int, choices=tipos_sede.keys())
    if tipo_id is None: return
    
    telefone = get_valid_input("Telefone da Sede (opcional): ", optional=True)

    print("\n--- Endereço da Sede ---")
    cep = get_valid_input("CEP: ")
    estado = get_valid_input("Estado: ")
    cidade = get_valid_input("Cidade: ")
    bairro = get_valid_input("Bairro: ")
    rua = get_valid_input("Rua: ")
    numero = get_valid_input("Número: ")
    complemento = get_valid_input("Complemento (opcional): ", optional=True)

    try:
        sql_insert_address = "INSERT INTO Endereco (CEP, Estado, Cidade, Bairro, Rua, Numero, Complemento) VALUES (?, ?, ?, ?, ?, ?, ?);"
        address_params = (cep, estado, cidade, bairro, rua, numero, complemento)
        new_address_id = db_connection.execute_insert_and_get_last_id(conn, sql_insert_address, address_params)

        if new_address_id is not None:
            # Verificar se o endereço já está em uso por outra sede
            if db_connection.execute_query(conn, "SELECT 1 FROM Sede WHERE ID_Endereco = ?", (new_address_id,), fetch_results=True):
                print("Erro: Este endereço já está cadastrado para outra sede.")
                # Idealmente, deletar o endereço recém-criado se não for usado.
                return

            sql_insert_sede = "INSERT INTO Sede (Tipo, ID_Endereco, Telefone) VALUES (?, ?, ?);"
            sede_params = (tipo_id, new_address_id, telefone)
            if db_connection.execute_query(conn, sql_insert_sede, sede_params):
                print("Sede e Endereço adicionados com sucesso!")
            else:
                print("Erro: Falha ao adicionar sede.")
        else:
            print("Erro: Falha ao adicionar endereço para a sede.")
    except Exception as e:
        print(f"Erro inesperado ao adicionar sede: {e}")

def list_headquarters_terminal(conn, simple_list=False):
    print("\n--- Lista de Sedes ---")
    sql = """
    SELECT S.ID_Sede, 
           CASE S.Tipo 
               WHEN 1 THEN 'Distribuição' 
               WHEN 2 THEN 'Loja' 
               WHEN 3 THEN 'Ambos' 
               ELSE 'Desconhecido' 
           END AS Tipo_Descricao,
           S.Telefone, E.Rua, E.Numero, E.Bairro, E.Cidade, E.Estado, E.CEP
    FROM Sede S
    INNER JOIN Endereco E ON S.ID_Endereco = E.ID_Endereco
    ORDER BY S.ID_Sede;
    """
    sedes = db_connection.execute_query(conn, sql, fetch_results=True)
    if sedes:
        if simple_list:
            print("{:<5} {:<15} {:<20}".format("ID", "Tipo", "Cidade"))
            print("-" * 40)
            for s in sedes:
                print("{:<5} {:<15} {:<20}".format(s[0], s[1], s[6])) # ID, Tipo, Cidade
            return

        headers = ["ID Sede", "Tipo", "Telefone", "Rua", "Nº", "Bairro", "Cidade", "UF", "CEP"]
        col_widths = [8, 15, 15, 20, 8, 15, 15, 5, 10]
        header_format = "".join([f"{{:<{w}}}" for w in col_widths])
        print(header_format.format(*headers))
        print("-" * sum(col_widths))
        for s in sedes:
            s_formatted = [str(x) if x is not None else "" for x in s]
            print(header_format.format(*s_formatted))
    else:
        print("Nenhuma sede encontrada.")

def update_headquarters_terminal(conn):
    print("\n--- Atualizar Sede ---")
    sede_id = get_valid_input("Digite o ID da Sede a ser atualizada: ", int)
    if sede_id is None: return

    sql_get_sede = """
    SELECT S.Tipo, S.Telefone, E.ID_Endereco, E.CEP, E.Estado, E.Cidade, E.Bairro, E.Rua, E.Numero, E.Complemento
    FROM Sede S INNER JOIN Endereco E ON S.ID_Endereco = E.ID_Endereco
    WHERE S.ID_Sede = ?;
    """
    current_data = db_connection.execute_query(conn, sql_get_sede, (sede_id,), fetch_results=True)
    if not current_data:
        print("Sede não encontrada.")
        return

    s_data = current_data[0]
    print(f"Atualizando Sede ID: {sede_id}")
    print("Deixe em branco para manter o valor atual.")

    tipos_sede = {1: "Distribuição", 2: "Loja", 3: "Ambos"}
    print(f"Tipo atual: {s_data[0]} - {tipos_sede.get(s_data[0], 'Desconhecido')}")
    for k,v in tipos_sede.items(): print(f"  {k} - {v}")
    new_tipo_id_str = input(f"Novo Tipo da Sede (ID) [{s_data[0]}]: ").strip()
    new_tipo_id = int(new_tipo_id_str) if new_tipo_id_str and new_tipo_id_str.isdigit() and int(new_tipo_id_str) in tipos_sede else s_data[0]

    new_telefone = input(f"Telefone [{s_data[1] or ''}]: ").strip() or s_data[1]

    address_id = s_data[2]
    print("\n--- Endereço da Sede ---")
    new_cep = input(f"CEP [{s_data[3]}]: ").strip() or s_data[3]
    new_state = input(f"Estado [{s_data[4]}]: ").strip() or s_data[4]
    new_city = input(f"Cidade [{s_data[5]}]: ").strip() or s_data[5]
    new_neighborhood = input(f"Bairro [{s_data[6]}]: ").strip() or s_data[6]
    new_street = input(f"Rua [{s_data[7]}]: ").strip() or s_data[7]
    new_number = input(f"Número [{s_data[8]}]: ").strip() or s_data[8]
    new_complement = input(f"Complemento [{s_data[9] or ''}]: ").strip() or s_data[9]

    try:
        sql_update_address = "UPDATE Endereco SET CEP=?, Estado=?, Cidade=?, Bairro=?, Rua=?, Numero=?, Complemento=? WHERE ID_Endereco=?;"
        db_connection.execute_query(conn, sql_update_address, (new_cep, new_state, new_city, new_neighborhood, new_street, new_number, new_complement, address_id))

        sql_update_sede = "UPDATE Sede SET Tipo=?, Telefone=? WHERE ID_Sede=?;"
        db_connection.execute_query(conn, sql_update_sede, (new_tipo_id, new_telefone, sede_id))
        print("Sede e Endereço atualizados com sucesso!")
    except Exception as e:
        print(f"Erro inesperado ao atualizar sede: {e}")

def delete_headquarters_terminal(conn):
    print("\n--- Deletar Sede ---")
    sede_id = get_valid_input("Digite o ID da Sede a ser deletada: ", int)
    if sede_id is None: return

    # Verificar dependências (Funcionario)
    if db_connection.execute_query(conn, "SELECT 1 FROM Funcionario WHERE ID_Sede = ?", (sede_id,), fetch_results=True):
        print("Erro: Sede está associada a funcionários. Desvincule-os primeiro.")
        return

    address_id_data = db_connection.execute_query(conn, "SELECT ID_Endereco FROM Sede WHERE ID_Sede = ?", (sede_id,), fetch_results=True)
    if not address_id_data:
        print("Sede não encontrada.")
        return
    
    confirm = input(f"Tem certeza que deseja deletar a sede ID {sede_id} e seu endereço? (s/n): ").strip().lower()
    if confirm != 's':
        print("Exclusão cancelada.")
        return

    try:
        if db_connection.execute_query(conn, "DELETE FROM Sede WHERE ID_Sede = ?", (sede_id,)):
            print("Sede deletada.")
            address_id = address_id_data[0][0]
            # Verificar se o endereço é usado por alguma Pessoa antes de deletar
            if not db_connection.execute_query(conn, "SELECT 1 FROM Pessoa WHERE ID_Endereco = ?", (address_id,), fetch_results=True):
                if db_connection.execute_query(conn, "DELETE FROM Endereco WHERE ID_Endereco = ?", (address_id,)):
                    print("Endereço associado à sede deletado com sucesso.")
                else:
                    print("Aviso: Sede deletada, mas falha ao deletar endereço.")
            else:
                print("Aviso: Sede deletada, mas o endereço não foi removido pois está em uso por Pessoas.")
        else:
            print("Erro: Falha ao deletar sede.")
    except Exception as e:
        print(f"Erro inesperado ao deletar sede: {e}")

# --- Gerenciar Produtos a Serem Entregues ---
def manage_products_terminal(conn):
    options = ["Adicionar Produto", "Listar Produtos", "Atualizar Produto", "Deletar Produto"]
    while True:
        clear_screen()
        choice = display_menu("Gerenciar Produtos a Serem Entregues", options)
        if choice == 1: add_product_terminal(conn)
        elif choice == 2: list_products_terminal(conn)
        elif choice == 3: update_product_terminal(conn)
        elif choice == 4: delete_product_terminal(conn)
        elif choice == 0: break
        press_enter_to_continue()

def add_product_terminal(conn):
    print("\n--- Adicionar Novo Produto a Ser Entregue ---")
    peso = get_valid_input("Peso do produto (kg): ", float)
    
    status_entrega_validos = ['Em Processamento', 'Aguardando Coleta', 'Em Transito', 'Entregue', 'Cancelado', 'Falha na Entrega']
    status_entrega = get_valid_input(f"Status Inicial ({', '.join(status_entrega_validos)}): ", choices=status_entrega_validos)
    
    data_chegada_cd_str = get_valid_input("Data de Chegada no Centro de Distribuição (AAAA-MM-DD): ")
    try:
        data_chegada_cd = datetime.strptime(data_chegada_cd_str, '%Y-%m-%d').date()
    except ValueError:
        print("Data de chegada inválida.")
        return

    data_prevista_entrega_str = get_valid_input("Data Prevista de Entrega (AAAA-MM-DD, opcional): ", optional=True)
    data_prevista_entrega = None
    if data_prevista_entrega_str:
        try:
            data_prevista_entrega = datetime.strptime(data_prevista_entrega_str, '%Y-%m-%d').date()
        except ValueError:
            print("Data prevista inválida. Deixando em branco.")

    tipos_produto_validos = ['Fragil', 'Perecivel', 'Comum']
    tipo_produto = get_valid_input(f"Tipo de Produto ({', '.join(tipos_produto_validos)}): ", choices=tipos_produto_validos)

    print("\n--- Remetente ---")
    list_people_terminal(conn) # Ajuda a escolher
    id_remetente = get_valid_input("Código Pessoa do Remetente (deve ser um Cliente existente): ", int)
    if not db_connection.execute_query(conn, "SELECT 1 FROM Cliente WHERE Codigo_Pessoa = ?", (id_remetente,), fetch_results=True):
        print("Erro: Remetente não encontrado como Cliente.")
        return

    print("\n--- Destinatário ---")
    list_people_terminal(conn) # Ajuda a escolher
    id_destinatario = get_valid_input("Código Pessoa do Destinatário (Pessoa existente): ", int)
    dest_pessoa_data = db_connection.execute_query(conn, "SELECT P.Nome, P.ID_Endereco, P.Telefone, C.CPF FROM Pessoa P LEFT JOIN Cliente C ON P.Codigo_Pessoa = C.Codigo_Pessoa WHERE P.Codigo_Pessoa = ?", (id_destinatario,), fetch_results=True)
    if not dest_pessoa_data:
        print("Erro: Destinatário (Pessoa) não encontrado.")
        return
    
    dest_nome, dest_id_endereco, dest_telefone, dest_cpf = dest_pessoa_data[0]
    
    # Dados para a tabela Dados_Rastreamento (snapshot)
    print("\n--- Dados para Rastreamento (Destinatário) ---")
    # Tenta preencher com dados da Pessoa Destinatário, mas permite sobrescrever
    dr_nome_dest = input(f"Nome do Destinatário para rastreamento [{dest_nome}]: ").strip() or dest_nome
    dr_cpf_dest = input(f"CPF do Destinatário para rastreamento [{dest_cpf or ''}]: ").strip() or dest_cpf
    
    # Endereço de entrega para o rastreamento (pode ser diferente do endereço principal da pessoa)
    print("O endereço de entrega para o rastreamento será o endereço principal do destinatário.")
    print("Se for um endereço diferente, você precisará cadastrá-lo e associá-lo ao Dados_Rastreamento manualmente após a criação do produto (via Gerenciar Rastreamento).")
    dr_id_endereco = dest_id_endereco # Usa o endereço principal do destinatário por padrão
    
    endereco_dest_data = db_connection.execute_query(conn, "SELECT Cidade, Estado FROM Endereco WHERE ID_Endereco = ?", (dr_id_endereco,), fetch_results=True)
    if not endereco_dest_data:
        print("Erro: Endereço do destinatário não encontrado.")
        return
    dr_cidade, dr_estado = endereco_dest_data[0]
    dr_telefone_dest = input(f"Telefone do Destinatário para rastreamento [{dest_telefone or ''}]: ").strip() or dest_telefone
    
    # Gerar código de rastreamento único (simplificado)
    # Em um sistema real, usar um algoritmo mais robusto ou UUID
    cod_rastreamento = f"SRL{datetime.now().strftime('%Y%m%d%H%M%S%f')}" 

    # Motorista (opcional neste momento)
    cod_motorista = None
    if input("Deseja atribuir um motorista agora? (s/n): ").lower() == 's':
        # Listar motoristas disponíveis
        sql_motoristas = """
        SELECT F.Codigo_Funcionario, P.Nome 
        FROM Funcionario F JOIN Pessoa P ON F.Codigo_Funcionario = P.Codigo_Pessoa
        WHERE F.Cargo = 'Motorista'
        ORDER BY P.Nome;
        """
        motoristas = db_connection.execute_query(conn, sql_motoristas, fetch_results=True)
        if motoristas:
            print("\n--- Motoristas Disponíveis ---")
            for m_cod, m_nome in motoristas:
                print(f"{m_cod} - {m_nome}")
            cod_motorista = get_valid_input("Código do Motorista (opcional): ", int, optional=True)
            if cod_motorista and not db_connection.execute_query(conn, "SELECT 1 FROM Funcionario WHERE Codigo_Funcionario = ? AND Cargo = 'Motorista'", (cod_motorista,), fetch_results=True):
                print("Motorista inválido. Deixando sem motorista.")
                cod_motorista = None
        else:
            print("Nenhum motorista cadastrado.")

    try:
        # 1. Inserir Dados_Rastreamento
        sql_insert_rastreamento = """
        INSERT INTO Dados_Rastreamento (Codigo_Rastreamento, Nome_Destinatario, CPF_Destinatario, ID_Endereco, Cidade, Estado, Telefone_Destinatario)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """
        params_rastreamento = (cod_rastreamento, dr_nome_dest, dr_cpf_dest, dr_id_endereco, dr_cidade, dr_estado, dr_telefone_dest)
        new_rastreamento_id = db_connection.execute_insert_and_get_last_id(conn, sql_insert_rastreamento, params_rastreamento)

        if new_rastreamento_id:
            # 2. Inserir Produto_A_Ser_Entregue
            sql_insert_produto = """
            INSERT INTO Produto_A_Ser_Entregue 
            (Peso, Status_Entrega, Data_Chegada_CD, Data_Prevista_Entrega, Tipo_Produto, ID_Remetente, ID_Destinatario, Codigo_Funcionario_Motorista, ID_Rastreamento)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """
            params_produto = (peso, status_entrega, data_chegada_cd, data_prevista_entrega, tipo_produto, 
                              id_remetente, id_destinatario, cod_motorista, new_rastreamento_id)
            
            if db_connection.execute_query(conn, sql_insert_produto, params_produto):
                print(f"Produto adicionado com sucesso! Código de Rastreamento: {cod_rastreamento}")
            else:
                print("Erro: Falha ao adicionar produto.")
                # Idealmente, deletar o Dados_Rastreamento recém-criado.
        else:
            print("Erro: Falha ao criar dados de rastreamento.")

    except Exception as e:
        print(f"Erro inesperado ao adicionar produto: {e}")

def list_products_terminal(conn, for_client_person_code=None):
    print("\n--- Lista de Produtos a Serem Entregues ---")
    
    base_sql = """
    SELECT 
        PROD.ID_Produto, PROD.Peso, PROD.Status_Entrega, PROD.Tipo_Produto,
        FORMAT(PROD.Data_Chegada_CD, 'dd/MM/yyyy') AS Data_Chegada_CD, 
        FORMAT(PROD.Data_Prevista_Entrega, 'dd/MM/yyyy') AS Data_Prevista_Entrega,
        REM.Nome AS Remetente, DESTP.Nome AS Destinatario_Pessoa, DR.Nome_Destinatario AS Destinatario_Rastr,
        DR.Codigo_Rastreamento, MOT.Nome AS Motorista
    FROM Produto_A_Ser_Entregue PROD
    INNER JOIN Pessoa REM ON PROD.ID_Remetente = REM.Codigo_Pessoa
    INNER JOIN Dados_Rastreamento DR ON PROD.ID_Rastreamento = DR.ID_Rastreamento
    INNER JOIN Pessoa DESTP ON PROD.ID_Destinatario = DESTP.Codigo_Pessoa -- Pessoa original do destinatário
    LEFT JOIN Funcionario FMOT ON PROD.Codigo_Funcionario_Motorista = FMOT.Codigo_Funcionario
    LEFT JOIN Pessoa MOT ON FMOT.Codigo_Funcionario = MOT.Codigo_Pessoa
    """
    params = []
    if for_client_person_code:
        base_sql += " WHERE PROD.ID_Remetente = ? OR PROD.ID_Destinatario = ?"
        params.extend([for_client_person_code, for_client_person_code])
    
    base_sql += " ORDER BY PROD.ID_Produto DESC;"

    products = db_connection.execute_query(conn, base_sql, tuple(params) if params else None, fetch_results=True)

    if products:
        headers = ["ID Prod", "Peso(kg)", "Status", "Tipo Prod", "Chegada CD", "Prev. Entrega", "Remetente", "Destinatário (Rastr.)", "Cód. Rastr.", "Motorista"]
        col_widths = [8, 8, 18, 12, 12, 15, 20, 20, 20, 20]
        header_format = "".join([f"{{:<{w}}}" for w in col_widths])
        print(header_format.format(*headers))
        print("-" * sum(col_widths))
        for p in products:
            p_formatted = [str(x) if x is not None else "" for x in (p[0], p[1], p[2], p[3], p[4], p[5], p[6], p[8], p[9], p[10])] # Ajuste nos índices para pegar Destinatario_Rastr
            print(header_format.format(*p_formatted))
    else:
        if for_client_person_code:
            print("Nenhum produto encontrado para você (como remetente ou destinatário).")
        else:
            print("Nenhum produto encontrado.")

def update_product_terminal(conn):
    print("\n--- Atualizar Produto a Ser Entregue ---")
    product_id = get_valid_input("Digite o ID do Produto a ser atualizado: ", int)
    if product_id is None: return

    sql_get_prod = """
    SELECT Peso, Status_Entrega, Data_Chegada_CD, Data_Prevista_Entrega, Tipo_Produto, 
           ID_Remetente, ID_Destinatario, Codigo_Funcionario_Motorista, ID_Rastreamento
    FROM Produto_A_Ser_Entregue WHERE ID_Produto = ?;
    """
    current_data = db_connection.execute_query(conn, sql_get_prod, (product_id,), fetch_results=True)
    if not current_data:
        print("Produto não encontrado.")
        return
    
    p_data = current_data[0]
    print(f"Atualizando Produto ID: {product_id}")
    print("Deixe em branco para manter o valor atual.")

    new_peso = input(f"Peso (kg) [{p_data[0]}]: ").strip()
    new_peso = float(new_peso) if new_peso else p_data[0]

    status_entrega_validos = ['Em Processamento', 'Aguardando Coleta', 'Em Transito', 'Entregue', 'Cancelado', 'Falha na Entrega']
    new_status = input(f"Status [{p_data[1]}] ({', '.join(status_entrega_validos)}): ").strip() or p_data[1]
    if new_status not in status_entrega_validos:
        print("Status inválido. Mantendo anterior.")
        new_status = p_data[1]

    new_data_chegada_cd_str = input(f"Data Chegada CD [{p_data[2]}] (AAAA-MM-DD): ").strip()
    new_data_chegada_cd = datetime.strptime(new_data_chegada_cd_str, '%Y-%m-%d').date() if new_data_chegada_cd_str else p_data[2]
    
    new_data_prev_ent_str = input(f"Data Prev. Entrega [{p_data[3] or ''}] (AAAA-MM-DD): ").strip()
    new_data_prev_ent = datetime.strptime(new_data_prev_ent_str, '%Y-%m-%d').date() if new_data_prev_ent_str else p_data[3]

    tipos_produto_validos = ['Fragil', 'Perecivel', 'Comum']
    new_tipo_prod = input(f"Tipo Produto [{p_data[4]}] ({', '.join(tipos_produto_validos)}): ").strip() or p_data[4]
    if new_tipo_prod not in tipos_produto_validos:
        print("Tipo de produto inválido. Mantendo anterior.")
        new_tipo_prod = p_data[4]

    # Remetente e Destinatário geralmente não são alterados após a criação.
    # Se necessário, seria uma lógica mais complexa ou cancelamento/recriação.
    print(f"Remetente (Cód: {p_data[5]}) e Destinatário (Cód: {p_data[6]}) não são alterados aqui.")
    new_id_remetente, new_id_destinatario = p_data[5], p_data[6]

    # Motorista
    sql_motoristas = "SELECT F.Codigo_Funcionario, P.Nome FROM Funcionario F JOIN Pessoa P ON F.Codigo_Funcionario = P.Codigo_Pessoa WHERE F.Cargo = 'Motorista' ORDER BY P.Nome;"
    motoristas = db_connection.execute_query(conn, sql_motoristas, fetch_results=True)
    if motoristas:
        print("\n--- Motoristas Disponíveis ---")
        for m_cod, m_nome in motoristas: print(f"{m_cod} - {m_nome}")
    new_cod_motorista_str = input(f"Código do Motorista [{p_data[7] or ''}] (deixe em branco ou 0 para nenhum): ").strip()
    new_cod_motorista = None
    if new_cod_motorista_str:
        try:
            val = int(new_cod_motorista_str)
            if val == 0:
                new_cod_motorista = None
            elif db_connection.execute_query(conn, "SELECT 1 FROM Funcionario WHERE Codigo_Funcionario = ? AND Cargo = 'Motorista'", (val,), fetch_results=True):
                new_cod_motorista = val
            else:
                print("Motorista inválido. Mantendo anterior.")
                new_cod_motorista = p_data[7]
        except ValueError:
            print("Código do motorista inválido. Mantendo anterior.")
            new_cod_motorista = p_data[7]
    else: # Se deixou em branco, mantém o anterior
        new_cod_motorista = p_data[7]


    # ID_Rastreamento também não é alterado aqui. Gerenciar via "Gerenciar Rastreamento".
    print(f"ID de Rastreamento ({p_data[8]}) não é alterado aqui.")

    sql_update_prod = """
    UPDATE Produto_A_Ser_Entregue 
    SET Peso=?, Status_Entrega=?, Data_Chegada_CD=?, Data_Prevista_Entrega=?, Tipo_Produto=?, Codigo_Funcionario_Motorista=?
    WHERE ID_Produto=?;
    """
    params = (new_peso, new_status, new_data_chegada_cd, new_data_prev_ent, new_tipo_prod, new_cod_motorista, product_id)
    if db_connection.execute_query(conn, sql_update_prod, params):
        print("Produto atualizado com sucesso!")
    else:
        print("Erro: Falha ao atualizar produto.")

def delete_product_terminal(conn):
    print("\n--- Deletar Produto a Ser Entregue ---")
    product_id = get_valid_input("Digite o ID do Produto a ser deletado: ", int)
    if product_id is None: return

    # Verificar dependências (Carregamento)
    if db_connection.execute_query(conn, "SELECT 1 FROM Carregamento WHERE ID_Produto = ?", (product_id,), fetch_results=True):
        print("Erro: Produto está associado a um carregamento. Remova-o do carregamento primeiro.")
        return

    prod_data = db_connection.execute_query(conn, "SELECT ID_Rastreamento, Status_Entrega FROM Produto_A_Ser_Entregue WHERE ID_Produto = ?", (product_id,), fetch_results=True)
    if not prod_data:
        print("Produto não encontrado.")
        return
    
    id_rastreamento = prod_data[0][0]
    status_atual = prod_data[0][1]

    if status_atual not in ['Cancelado', 'Em Processamento']: # Regra de negócio exemplo
        print(f"Aviso: O produto está com status '{status_atual}'. A exclusão pode não ser permitida dependendo das regras de negócio.")
        if input("Continuar com a exclusão? (s/n): ").lower() != 's':
            print("Exclusão cancelada.")
            return
    
    confirm = input(f"Tem certeza que deseja deletar o Produto ID {product_id} e seus Dados de Rastreamento associados? (s/n): ").strip().lower()
    if confirm != 's':
        print("Exclusão cancelada.")
        return

    try:
        # 1. Deletar da tabela Carregamento (se houver constraint, ou se quiser limpar)
        # db_connection.execute_query(conn, "DELETE FROM Carregamento WHERE ID_Produto = ?", (product_id,))
        
        # 2. Deletar Produto
        if db_connection.execute_query(conn, "DELETE FROM Produto_A_Ser_Entregue WHERE ID_Produto = ?", (product_id,)):
            print("Produto deletado.")
            # 3. Deletar Dados_Rastreamento associados
            if db_connection.execute_query(conn, "DELETE FROM Dados_Rastreamento WHERE ID_Rastreamento = ?", (id_rastreamento,)):
                print("Dados de rastreamento associados deletados com sucesso.")
            else:
                print("Aviso: Produto deletado, mas falha ao deletar dados de rastreamento.")
        else:
            print("Erro: Falha ao deletar produto.")
    except Exception as e:
        print(f"Erro inesperado ao deletar produto: {e}")

# --- Gerenciar Dados de Rastreamento (CRUD mais para fins administrativos) ---
def manage_tracking_terminal(conn):
    options = ["Adicionar Dados de Rastreamento (Avançado)", "Listar Dados de Rastreamento", "Atualizar Dados de Rastreamento", "Deletar Dados de Rastreamento"]
    while True:
        clear_screen()
        choice = display_menu("Gerenciar Dados de Rastreamento", options)
        if choice == 1: add_tracking_data_terminal(conn) # Geralmente criado com o produto
        elif choice == 2: list_tracking_data_terminal(conn)
        elif choice == 3: update_tracking_data_terminal(conn)
        elif choice == 4: delete_tracking_data_terminal(conn)
        elif choice == 0: break
        press_enter_to_continue()

def add_tracking_data_terminal(conn):
    print("\n--- Adicionar Dados de Rastreamento (Uso Administrativo) ---")
    print("Normalmente, os dados de rastreamento são criados automaticamente com um Produto.")
    
    codigo_rastreamento = get_valid_input("Código de Rastreamento (único): ")
    if db_connection.execute_query(conn, "SELECT 1 FROM Dados_Rastreamento WHERE Codigo_Rastreamento = ?", (codigo_rastreamento,), fetch_results=True):
        print("Erro: Código de Rastreamento já existe.")
        return

    nome_dest = get_valid_input("Nome do Destinatário: ")
    cpf_dest = get_valid_input("CPF do Destinatário (opcional): ", optional=True)
    
    print("\n--- Endereço de Entrega (para o rastreamento) ---")
    list_people_terminal(conn) # Mostrar pessoas para ajudar a encontrar um endereço existente
    print("Você pode selecionar um ID de Endereço existente ou cadastrar um novo.")
    id_endereco = get_valid_input("ID do Endereço de entrega (de um endereço já cadastrado): ", int)
    addr_data = db_connection.execute_query(conn, "SELECT Cidade, Estado FROM Endereco WHERE ID_Endereco = ?", (id_endereco,), fetch_results=True)
    if not addr_data:
        print("Erro: ID de Endereço não encontrado. Cadastre o endereço primeiro.")
        return
    cidade, estado = addr_data[0]
    
    telefone_dest = get_valid_input("Telefone do Destinatário (opcional): ", optional=True)

    sql = """
    INSERT INTO Dados_Rastreamento (Codigo_Rastreamento, Nome_Destinatario, CPF_Destinatario, ID_Endereco, Cidade, Estado, Telefone_Destinatario)
    VALUES (?, ?, ?, ?, ?, ?, ?);
    """
    params = (codigo_rastreamento, nome_dest, cpf_dest, id_endereco, cidade, estado, telefone_dest)
    if db_connection.execute_insert_and_get_last_id(conn, sql, params):
        print("Dados de rastreamento adicionados com sucesso!")
    else:
        print("Erro: Falha ao adicionar dados de rastreamento.")

def list_tracking_data_terminal(conn):
    print("\n--- Lista de Dados de Rastreamento ---")
    sql = """
    SELECT DR.ID_Rastreamento, DR.Codigo_Rastreamento, DR.Nome_Destinatario, DR.CPF_Destinatario,
           DR.ID_Endereco, E.Rua, E.Numero, E.Cidade AS Cidade_Entrega, E.Estado AS UF_Entrega, DR.Telefone_Destinatario,
           P.ID_Produto
    FROM Dados_Rastreamento DR
    INNER JOIN Endereco E ON DR.ID_Endereco = E.ID_Endereco
    LEFT JOIN Produto_A_Ser_Entregue P ON DR.ID_Rastreamento = P.ID_Rastreamento /* Para ver se está associado */
    ORDER BY DR.ID_Rastreamento DESC;
    """
    tracking_data = db_connection.execute_query(conn, sql, fetch_results=True)
    if tracking_data:
        headers = ["ID Rastr.", "Cód. Rastr.", "Nome Dest.", "CPF Dest.", "ID End.", "Rua Entrega", "Nº", "Cidade Entr.", "UF", "Tel. Dest.", "ID Produto Assoc."]
        col_widths = [10, 18, 20, 15, 8, 20, 8, 15, 5, 15, 15]
        header_format = "".join([f"{{:<{w}}}" for w in col_widths])
        print(header_format.format(*headers))
        print("-" * sum(col_widths))
        for td in tracking_data:
            td_formatted = [str(x) if x is not None else "" for x in td]
            print(header_format.format(*td_formatted))
    else:
        print("Nenhum dado de rastreamento encontrado.")

def update_tracking_data_terminal(conn):
    print("\n--- Atualizar Dados de Rastreamento ---")
    tracking_id = get_valid_input("Digite o ID de Rastreamento a ser atualizado: ", int)
    if tracking_id is None: return

    sql_get_track = """
    SELECT Codigo_Rastreamento, Nome_Destinatario, CPF_Destinatario, ID_Endereco, Cidade, Estado, Telefone_Destinatario
    FROM Dados_Rastreamento WHERE ID_Rastreamento = ?;
    """
    current_data = db_connection.execute_query(conn, sql_get_track, (tracking_id,), fetch_results=True)
    if not current_data:
        print("Dados de rastreamento não encontrados.")
        return

    t_data = current_data[0]
    print(f"Atualizando Rastreamento ID: {tracking_id}")
    print("Deixe em branco para manter o valor atual.")

    new_cod_rastr = input(f"Código de Rastreamento [{t_data[0]}]: ").strip() or t_data[0]
    if new_cod_rastr != t_data[0] and db_connection.execute_query(conn, "SELECT 1 FROM Dados_Rastreamento WHERE Codigo_Rastreamento = ? AND ID_Rastreamento != ?", (new_cod_rastr, tracking_id), fetch_results=True):
        print("Erro: Novo código de rastreamento já existe. Mantendo anterior.")
        new_cod_rastr = t_data[0]

    new_nome_dest = input(f"Nome Destinatário [{t_data[1]}]: ").strip() or t_data[1]
    new_cpf_dest = input(f"CPF Destinatário [{t_data[2] or ''}]: ").strip() or t_data[2]
    
    print(f"ID Endereço atual: {t_data[3]}. Para alterar o endereço, forneça um novo ID de Endereço existente.")
    new_id_endereco_str = input(f"Novo ID Endereço [{t_data[3]}]: ").strip()
    new_id_endereco = int(new_id_endereco_str) if new_id_endereco_str else t_data[3]
    
    new_cidade, new_estado = t_data[4], t_data[5]
    if new_id_endereco != t_data[3]: # Se o ID do endereço mudou, buscar nova cidade/estado
        addr_data = db_connection.execute_query(conn, "SELECT Cidade, Estado FROM Endereco WHERE ID_Endereco = ?", (new_id_endereco,), fetch_results=True)
        if not addr_data:
            print("Erro: Novo ID de Endereço não encontrado. Mantendo endereço anterior.")
            new_id_endereco = t_data[3] # Reverte para o ID anterior
            # new_cidade, new_estado já são os anteriores
        else:
            new_cidade, new_estado = addr_data[0]
    
    new_tel_dest = input(f"Telefone Destinatário [{t_data[6] or ''}]: ").strip() or t_data[6]

    sql_update_track = """
    UPDATE Dados_Rastreamento 
    SET Codigo_Rastreamento=?, Nome_Destinatario=?, CPF_Destinatario=?, ID_Endereco=?, Cidade=?, Estado=?, Telefone_Destinatario=?
    WHERE ID_Rastreamento=?;
    """
    params = (new_cod_rastr, new_nome_dest, new_cpf_dest, new_id_endereco, new_cidade, new_estado, new_tel_dest, tracking_id)
    if db_connection.execute_query(conn, sql_update_track, params):
        print("Dados de rastreamento atualizados com sucesso!")
    else:
        print("Erro: Falha ao atualizar dados de rastreamento.")

def delete_tracking_data_terminal(conn):
    print("\n--- Deletar Dados de Rastreamento ---")
    tracking_id = get_valid_input("Digite o ID de Rastreamento a ser deletado: ", int)
    if tracking_id is None: return

    # Verificar se está associado a um Produto_A_Ser_Entregue
    if db_connection.execute_query(conn, "SELECT 1 FROM Produto_A_Ser_Entregue WHERE ID_Rastreamento = ?", (tracking_id,), fetch_results=True):
        print("Erro: Estes dados de rastreamento estão vinculados a um produto.")
        print("Delete o produto associado primeiro (isso também deveria deletar os dados de rastreamento), ou desvincule-os.")
        return
    
    if not db_connection.execute_query(conn, "SELECT 1 FROM Dados_Rastreamento WHERE ID_Rastreamento = ?", (tracking_id,), fetch_results=True):
        print("Dados de rastreamento não encontrados.")
        return

    confirm = input(f"Tem certeza que deseja deletar os Dados de Rastreamento ID {tracking_id}? (s/n): ").strip().lower()
    if confirm != 's':
        print("Exclusão cancelada.")
        return

    if db_connection.execute_query(conn, "DELETE FROM Dados_Rastreamento WHERE ID_Rastreamento = ?", (tracking_id,)):
        print("Dados de rastreamento deletados com sucesso!")
    else:
        print("Erro: Falha ao deletar dados de rastreamento.")

# --- Gerenciar Carregamentos ---
def manage_shipments_terminal(conn):
    options = ["Adicionar Carregamento", "Listar Carregamentos", "Detalhes do Carregamento", "Remover Produto do Carregamento", "Deletar Carregamento"]
    while True:
        clear_screen()
        choice = display_menu("Gerenciar Carregamentos", options)
        if choice == 1: add_shipment_terminal(conn)
        elif choice == 2: list_shipments_terminal(conn)
        elif choice == 3: shipment_details_terminal(conn)
        elif choice == 4: remove_product_from_shipment_terminal(conn)
        elif choice == 5: delete_shipment_terminal(conn)
        elif choice == 0: break
        press_enter_to_continue()

def add_shipment_terminal(conn):
    print("\n--- Adicionar Novo Carregamento ---")
    list_available_vehicles(conn)
    placa_veiculo = get_valid_input("Placa do Veículo para o carregamento: ", str.upper)
    vehicle_data = db_connection.execute_query(conn, "SELECT Carga_Suportada, Status FROM Veiculo WHERE Placa_Veiculo = ?", (placa_veiculo,), fetch_results=True)
    if not vehicle_data:
        print("Erro: Veículo não encontrado.")
        return
    carga_max_veiculo, status_veiculo = vehicle_data[0]
    # if status_veiculo == 'Indisponivel':
    #     print(f"Aviso: Veículo {placa_veiculo} está atualmente Indisponível.")
        # if input("Continuar mesmo assim? (s/n):").lower() != 's': return

    data_carregamento_str = get_valid_input("Data do Carregamento (AAAA-MM-DD HH:MM, opcional, Enter para agora): ", optional=True)
    data_carregamento = datetime.now()
    if data_carregamento_str:
        try:
            data_carregamento = datetime.strptime(data_carregamento_str, '%Y-%m-%d %H:%M')
        except ValueError:
            print("Formato de data/hora inválido. Usando data/hora atual.")

    produtos_no_carregamento = []
    peso_total_carregamento = 0.0

    while True:
        print("\n--- Adicionar Produto ao Carregamento ---")
        print(f"Veículo: {placa_veiculo}, Carga Máx: {carga_max_veiculo}kg, Peso Atual: {peso_total_carregamento:.2f}kg")
        
        # Listar produtos que podem ser adicionados (ex: status 'Em Processamento' ou 'Aguardando Coleta')
        sql_produtos_disponiveis = """
        SELECT ID_Produto, Peso, Status_Entrega, Tipo_Produto, DR.Codigo_Rastreamento
        FROM Produto_A_Ser_Entregue P
        JOIN Dados_Rastreamento DR ON P.ID_Rastreamento = DR.ID_Rastreamento
        WHERE P.Status_Entrega IN ('Em Processamento', 'Aguardando Coleta')
          AND P.ID_Produto NOT IN (SELECT ID_Produto FROM Carregamento WHERE Placa_Veiculo = ? AND Data_Carregamento = ?) /* Evitar adicionar o mesmo produto duas vezes no mesmo carregamento */
          AND P.ID_Produto NOT IN ({}) /* Evitar adicionar produtos já selecionados para este carregamento */
        ORDER BY P.ID_Produto;
        """.format(','.join(map(str, produtos_no_carregamento)) if produtos_no_carregamento else '0') # Placeholder se lista vazia

        # print(sql_produtos_disponiveis) # Debug
        # print(placa_veiculo, data_carregamento) # Debug

        available_products = db_connection.execute_query(conn, sql_produtos_disponiveis, (placa_veiculo, data_carregamento), fetch_results=True)
        
        if not available_products:
            print("Nenhum produto disponível para adicionar (ou todos já foram selecionados).")
            if not produtos_no_carregamento: # Se nenhum produto foi adicionado ainda, cancela
                return
            break 
        
        print("\nProdutos disponíveis para este carregamento:")
        headers = ["ID Prod", "Peso(kg)", "Status", "Tipo", "Cód. Rastr."]
        col_widths = [8, 10, 18, 12, 20]
        header_format = "".join([f"{{:<{w}}}" for w in col_widths])
        print(header_format.format(*headers))
        print("-" * sum(col_widths))
        prod_dict = {}
        for p_id, p_peso, p_status, p_tipo, p_rastr in available_products:
            prod_dict[p_id] = {'peso': p_peso, 'status': p_status, 'tipo': p_tipo, 'rastr': p_rastr}
            print(header_format.format(p_id, p_peso, p_status, p_tipo, p_rastr))

        id_produto_str = input("Digite o ID do Produto para adicionar (ou 0 para finalizar): ").strip()
        if not id_produto_str.isdigit():
            print("ID inválido.")
            continue
        id_produto = int(id_produto_str)

        if id_produto == 0:
            if not produtos_no_carregamento:
                print("Nenhum produto adicionado ao carregamento.")
                return
            break
        
        if id_produto not in prod_dict:
            print("Produto não disponível ou ID inválido.")
            continue
        
        produto_selecionado = prod_dict[id_produto]
        if peso_total_carregamento + produto_selecionado['peso'] > carga_max_veiculo:
            print(f"Erro: Adicionar este produto ({produto_selecionado['peso']}kg) excederia a carga suportada do veículo ({carga_max_veiculo}kg).")
            print(f"Espaço restante: {carga_max_veiculo - peso_total_carregamento:.2f}kg")
            continue
        
        # Adicionar à lista e atualizar peso
        produtos_no_carregamento.append(id_produto)
        peso_total_carregamento += produto_selecionado['peso']
        print(f"Produto ID {id_produto} adicionado. Peso total atual: {peso_total_carregamento:.2f}kg")

    if not produtos_no_carregamento:
        print("Nenhum produto selecionado para o carregamento.")
        return

    try:
        # Inserir cada produto no carregamento
        # O ID_Carregamento é auto-incremental, então cada linha na tabela Carregamento
        # representa um item de um carregamento específico (identificado por Placa_Veiculo e Data_Carregamento).
        # O script SQL original tem ID_Carregamento como PK, e uma constraint UNIQUE (Placa_Veiculo, ID_Produto, Data_Carregamento).
        # Isso significa que um produto só pode estar uma vez em um "evento de carregamento" específico.
        
        num_sucessos = 0
        for prod_id in produtos_no_carregamento:
            sql_insert_carreg = "INSERT INTO Carregamento (Placa_Veiculo, ID_Produto, Data_Carregamento) VALUES (?, ?, ?);"
            if db_connection.execute_query(conn, sql_insert_carreg, (placa_veiculo, prod_id, data_carregamento)):
                num_sucessos += 1
                # Opcional: Atualizar status do produto para 'Em Transito' ou similar
                # db_connection.execute_query(conn, "UPDATE Produto_A_Ser_Entregue SET Status_Entrega = 'Em Transito' WHERE ID_Produto = ?", (prod_id,))
            else:
                print(f"Aviso: Falha ao adicionar produto ID {prod_id} ao carregamento (pode já existir para esta data/veículo).")
        
        if num_sucessos > 0:
            print(f"{num_sucessos} produto(s) registrados no carregamento para o veículo {placa_veiculo} em {data_carregamento.strftime('%d/%m/%Y %H:%M')}.")
            # Opcional: Atualizar status do veículo para 'Indisponivel' ou 'Em Rota'
            # db_connection.execute_query(conn, "UPDATE Veiculo SET Status = 'Indisponivel' WHERE Placa_Veiculo = ?", (placa_veiculo,))
        else:
            print("Nenhum produto foi efetivamente adicionado ao carregamento.")

    except Exception as e:
        print(f"Erro inesperado ao adicionar carregamento: {e}")

def list_shipments_terminal(conn):
    print("\n--- Lista de Carregamentos (Agrupados por Veículo e Data) ---")
    # Agrupa para mostrar "eventos" de carregamento
    sql = """
    SELECT 
        C.Placa_Veiculo, 
        FORMAT(C.Data_Carregamento, 'dd/MM/yyyy HH:mm') AS DataHora_Carregamento,
        COUNT(C.ID_Produto) AS Quantidade_Produtos,
        SUM(P.Peso) AS Peso_Total_Estimado_kg,
        V.Tipo AS Tipo_Veiculo,
        GROUP_CONCAT(P.ID_Produto) AS IDs_Produtos /* SQLite specific, SQL Server uses STRING_AGG */
        /* Para SQL Server: STRING_AGG(CAST(P.ID_Produto AS VARCHAR(10)), ', ') WITHIN GROUP (ORDER BY P.ID_Produto) AS IDs_Produtos */
    FROM Carregamento C
    JOIN Produto_A_Ser_Entregue P ON C.ID_Produto = P.ID_Produto
    JOIN Veiculo V ON C.Placa_Veiculo = V.Placa_Veiculo
    GROUP BY C.Placa_Veiculo, C.Data_Carregamento, V.Tipo
    ORDER BY C.Data_Carregamento DESC, C.Placa_Veiculo;
    """
    # Nota: GROUP_CONCAT é do SQLite. Para SQL Server, seria STRING_AGG.
    # Como o pyodbc pode estar conectado a diferentes bancos, a query pode precisar de ajuste.
    # Para simplificar a exibição no terminal sem STRING_AGG, vamos listar individualmente ou buscar detalhes.

    # Query simplificada para listar todos os registros de Carregamento:
    sql_simple = """
    SELECT C.ID_Carregamento, C.Placa_Veiculo, FORMAT(C.Data_Carregamento, 'dd/MM/yyyy HH:mm') AS DataHora,
           C.ID_Produto, P.Tipo_Produto, P.Peso, DR.Codigo_Rastreamento
    FROM Carregamento C
    JOIN Produto_A_Ser_Entregue P ON C.ID_Produto = P.ID_Produto
    JOIN Dados_Rastreamento DR ON P.ID_Rastreamento = DR.ID_Rastreamento
    ORDER BY C.Data_Carregamento DESC, C.Placa_Veiculo, C.ID_Carregamento;
    """
    shipments = db_connection.execute_query(conn, sql_simple, fetch_results=True)

    if shipments:
        print("Cada linha representa um produto em um carregamento.")
        headers = ["ID Carreg.", "Placa Veíc.", "Data/Hora Carreg.", "ID Prod.", "Tipo Prod.", "Peso Prod.", "Cód. Rastr."]
        col_widths = [10, 12, 18, 8, 15, 10, 20]
        header_format = "".join([f"{{:<{w}}}" for w in col_widths])
        print(header_format.format(*headers))
        print("-" * sum(col_widths))
        for s in shipments:
            s_formatted = [str(x) if x is not None else "" for x in s]
            print(header_format.format(*s_formatted))
        print("\nUse 'Detalhes do Carregamento' para ver agrupado.")
    else:
        print("Nenhum carregamento encontrado.")

def shipment_details_terminal(conn):
    print("\n--- Detalhes do Carregamento ---")
    placa = get_valid_input("Placa do Veículo: ", str.upper)
    data_carreg_str = get_valid_input("Data do Carregamento (AAAA-MM-DD HH:MM): ")
    try:
        data_carreg = datetime.strptime(data_carreg_str, '%Y-%m-%d %H:%M')
    except ValueError:
        print("Formato de data/hora inválido.")
        return

    sql_details = """
    SELECT C.ID_Carregamento, C.ID_Produto, P.Tipo_Produto, P.Peso, P.Status_Entrega, DR.Codigo_Rastreamento
    FROM Carregamento C
    JOIN Produto_A_Ser_Entregue P ON C.ID_Produto = P.ID_Produto
    JOIN Dados_Rastreamento DR ON P.ID_Rastreamento = DR.ID_Rastreamento
    WHERE C.Placa_Veiculo = ? AND C.Data_Carregamento = ?
    ORDER BY C.ID_Produto;
    """
    details = db_connection.execute_query(conn, sql_details, (placa, data_carreg), fetch_results=True)

    if details:
        print(f"\nDetalhes do Carregamento - Veículo: {placa}, Data: {data_carreg.strftime('%d/%m/%Y %H:%M')}")
        headers = ["ID Carreg. (Item)", "ID Prod.", "Tipo Prod.", "Peso Prod.", "Status Prod.", "Cód. Rastr."]
        col_widths = [18, 8, 15, 10, 18, 20]
        header_format = "".join([f"{{:<{w}}}" for w in col_widths])
        print(header_format.format(*headers))
        print("-" * sum(col_widths))
        total_peso = 0
        for d_id_carr, d_id_prod, d_tipo, d_peso, d_status, d_rastr in details:
            print(header_format.format(d_id_carr, d_id_prod, d_tipo, d_peso, d_status, d_rastr))
            total_peso += d_peso
        print("-" * sum(col_widths))
        print(f"Total de Produtos: {len(details)}, Peso Total Estimado: {total_peso:.2f} kg")
    else:
        print("Nenhum detalhe encontrado para este veículo e data de carregamento.")

def remove_product_from_shipment_terminal(conn):
    print("\n--- Remover Produto do Carregamento ---")
    # Para remover, precisamos do ID_Carregamento específico do item,
    # ou da combinação Placa, Data E ID_Produto.
    # A tabela Carregamento tem ID_Carregamento como PK.
    
    list_shipments_terminal(conn) # Mostra todos os itens para ajudar a escolher
    id_carregamento_item = get_valid_input("Digite o ID do Item de Carregamento a ser removido (da lista acima): ", int)
    if id_carregamento_item is None: return

    item_data = db_connection.execute_query(conn, "SELECT Placa_Veiculo, ID_Produto, Data_Carregamento FROM Carregamento WHERE ID_Carregamento = ?", (id_carregamento_item,), fetch_results=True)
    if not item_data:
        print("Item de carregamento não encontrado.")
        return
    
    placa, prod_id, data_carr = item_data[0]
    confirm = input(f"Tem certeza que deseja remover o produto ID {prod_id} do carregamento do veículo {placa} de {data_carr.strftime('%d/%m/%Y %H:%M')} (Item ID: {id_carregamento_item})? (s/n): ").lower()
    if confirm != 's':
        print("Remoção cancelada.")
        return
    
    if db_connection.execute_query(conn, "DELETE FROM Carregamento WHERE ID_Carregamento = ?", (id_carregamento_item,)):
        print("Produto removido do carregamento com sucesso.")
        # Opcional: Atualizar status do produto se necessário
    else:
        print("Erro ao remover produto do carregamento.")

def delete_shipment_terminal(conn):
    print("\n--- Deletar Carregamento Completo (Todos os Produtos) ---")
    placa = get_valid_input("Placa do Veículo do carregamento a ser deletado: ", str.upper)
    data_carreg_str = get_valid_input("Data do Carregamento (AAAA-MM-DD HH:MM) a ser deletado: ")
    try:
        data_carreg = datetime.strptime(data_carreg_str, '%Y-%m-%d %H:%M')
    except ValueError:
        print("Formato de data/hora inválido.")
        return

    # Verificar se existem itens para este carregamento
    items = db_connection.execute_query(conn, "SELECT ID_Carregamento FROM Carregamento WHERE Placa_Veiculo = ? AND Data_Carregamento = ?", (placa, data_carreg), fetch_results=True)
    if not items:
        print("Nenhum carregamento encontrado para este veículo e data para deletar.")
        return

    confirm = input(f"Tem certeza que deseja deletar TODOS os {len(items)} produtos do carregamento do veículo {placa} de {data_carreg.strftime('%d/%m/%Y %H:%M')}? (s/n): ").lower()
    if confirm != 's':
        print("Exclusão cancelada.")
        return
    
    if db_connection.execute_query(conn, "DELETE FROM Carregamento WHERE Placa_Veiculo = ? AND Data_Carregamento = ?", (placa, data_carreg)):
        print(f"Carregamento de {data_carreg.strftime('%d/%m/%Y %H:%M')} para o veículo {placa} deletado com sucesso.")
        # Opcional: Atualizar status dos produtos e do veículo se necessário
    else:
        print("Erro ao deletar o carregamento.")


# ------------------- SELF-SERVICE CLIENTE ----------------------
def cadastro_cliente_self_service(conn):
    clear_screen()
    print("--- Cadastro de Novo Cliente (Self-Service) ---")

    # 1. Coletar dados da Pessoa e Endereço
    print("\n--- Seus Dados Pessoais ---")
    nome = get_valid_input("Nome completo: ")
    rg = get_valid_input("RG (opcional): ", optional=True)
    telefone = get_valid_input("Telefone de contato: ")
    email = get_valid_input("Email: ")

    print("\n--- Seu Endereço Principal ---")
    cep = get_valid_input("CEP: ")
    estado = get_valid_input("Estado (UF): ")
    cidade = get_valid_input("Cidade: ")
    bairro = get_valid_input("Bairro: ")
    rua = get_valid_input("Rua/Avenida: ")
    numero = get_valid_input("Número: ")
    complemento = get_valid_input("Complemento (ex: Apt, Bloco, Casa): ", optional=True)

    # 2. Coletar dados específicos do Cliente (PF/PJ)
    print("\n--- Tipo de Cliente ---")
    tipo_cliente = get_valid_input("Você é Pessoa Física (PF) ou Jurídica (PJ)? ", str.upper, choices=['PF', 'PJ'])
    
    cpf, data_nasc_obj, cnpj, nome_empresa = None, None, None, None
    if tipo_cliente == 'PF':
        cpf = get_valid_input("CPF: ")
        data_nasc_str = get_valid_input("Data de Nascimento (AAAA-MM-DD): ")
        try:
            data_nasc_obj = datetime.strptime(data_nasc_str, "%Y-%m-%d").date()
        except ValueError:
            print("Formato de data inválido. Cadastro cancelado.")
            return
    else: # PJ
        cnpj = get_valid_input("CNPJ: ")
        nome_empresa = get_valid_input("Nome da Empresa/Razão Social: ")

    # 3. Coletar dados do Usuário
    print("\n--- Dados de Acesso ao Sistema ---")
    login = get_valid_input("Escolha um Login (nome de usuário): ")
    # Verificar se login já existe
    if db_connection.execute_query(conn, "SELECT 1 FROM Usuario WHERE Login = ?", (login,), fetch_results=True):
        print("Erro: Este login já está em uso. Por favor, escolha outro. Cadastro cancelado.")
        return
    
    senha = ""
    while not senha:
        senha = getpass.getpass("Crie uma Senha: ").strip()
        if not senha: print("Senha não pode ser vazia.")
    senha_confirm = getpass.getpass("Confirme a Senha: ").strip()
    if senha != senha_confirm:
        print("As senhas não coincidem. Cadastro cancelado.")
        return

    try:
        # Iniciar transação (conceitualmente, pyodbc não tem begin explicito fácil, commit/rollback no final)
        
        # Inserir Endereço
        sql_endereco = "INSERT INTO Endereco (CEP, Estado, Cidade, Bairro, Rua, Numero, Complemento) VALUES (?, ?, ?, ?, ?, ?, ?)"
        endereco_id = db_connection.execute_insert_and_get_last_id(conn, sql_endereco, (cep, estado, cidade, bairro, rua, numero, complemento))
        if not endereco_id:
            print("Erro crítico ao salvar endereço. Cadastro cancelado.")
            conn.rollback() # Garantir rollback se algo deu errado
            return

        # Inserir Pessoa
        sql_pessoa = "INSERT INTO Pessoa (Nome, RG, Telefone, Email, ID_Endereco) VALUES (?, ?, ?, ?, ?)"
        pessoa_id = db_connection.execute_insert_and_get_last_id(conn, sql_pessoa, (nome, rg, telefone, email, endereco_id))
        if not pessoa_id:
            print("Erro crítico ao salvar dados pessoais. Cadastro cancelado.")
            conn.rollback()
            return
            
        # Inserir Cliente
        sql_cliente = "INSERT INTO Cliente (Codigo_Pessoa, Tipo_Cliente, CPF, Data_Nascimento, CNPJ, Nome_Empresa) VALUES (?, ?, ?, ?, ?, ?)"
        if not db_connection.execute_query(conn, sql_cliente, (pessoa_id, tipo_cliente, cpf, data_nasc_obj, cnpj, nome_empresa)):
            print("Erro crítico ao salvar dados de cliente. Verifique os campos e tente novamente. Cadastro cancelado.")
            conn.rollback()
            return

        # Inserir Usuário
        hashed_senha = hash_password(senha)
        sql_usuario = "INSERT INTO Usuario (Login, Senha_Hash, Codigo_Pessoa, Tipo_Usuario) VALUES (?, ?, ?, ?)"
        if not db_connection.execute_query(conn, sql_usuario, (login, hashed_senha, pessoa_id, 'Cliente')):
            print("Erro crítico ao criar seu usuário de acesso. Cadastro cancelado.")
            conn.rollback()
            return

        # conn.commit() # Se tudo deu certo até aqui. execute_query e execute_insert_and_get_last_id já fazem commit individual.
        # Para uma transação real, o commit seria único no final.
        print("\nCadastro realizado com sucesso! Você já pode fazer login com seu novo usuário e senha.")

    except Exception as e:
        print(f"Ocorreu um erro inesperado durante o cadastro: {e}")
        try:
            conn.rollback() # Tenta reverter em caso de erro inesperado
        except Exception as rb_e:
            print(f"Erro adicional ao tentar reverter transação: {rb_e}")


# ------------------- MENUS DE USUÁRIOS ----------------------
def menu_cliente(conn, user_login, person_code):
    clear_screen()
    print(f"Bem-vindo(a) de volta, {user_login}!")
    
    options = [
        "Rastrear um Pedido",
        "Ver Meus Pedidos (como Remetente ou Destinatário)",
        "Ver/Atualizar Meus Dados Pessoais",
        "Ver/Atualizar Meus Endereços" # Poderia ser mais granular
    ]
    while True:
        clear_screen()
        choice = display_menu(f"Menu do Cliente - {user_login}", options)

        if choice == 1:
            cod_rastreio = get_valid_input("Digite o Código de Rastreamento do pedido: ")
            if cod_rastreio:
                sql_rastreio = """
                SELECT P.ID_Produto, P.Status_Entrega, P.Tipo_Produto, 
                       FORMAT(P.Data_Chegada_CD, 'dd/MM/yyyy') AS Chegada_CD, 
                       FORMAT(P.Data_Prevista_Entrega, 'dd/MM/yyyy') AS Prev_Entrega,
                       REM.Nome AS Remetente, DR.Nome_Destinatario AS Destinatario,
                       MOT.Nome AS Motorista, V.Placa_Veiculo, V.Tipo AS Tipo_Veiculo
                FROM Produto_A_Ser_Entregue P
                JOIN Dados_Rastreamento DR ON P.ID_Rastreamento = DR.ID_Rastreamento
                JOIN Pessoa REM ON P.ID_Remetente = REM.Codigo_Pessoa
                LEFT JOIN Funcionario FMOT ON P.Codigo_Funcionario_Motorista = FMOT.Codigo_Funcionario
                LEFT JOIN Pessoa MOT ON FMOT.Codigo_Funcionario = MOT.Codigo_Pessoa
                LEFT JOIN Veiculo V ON FMOT.Placa_Veiculo = V.Placa_Veiculo
                WHERE DR.Codigo_Rastreamento = ? 
                  AND (P.ID_Remetente = ? OR P.ID_Destinatario = ? OR DR.CPF_Destinatario = (SELECT CPF FROM Cliente WHERE Codigo_Pessoa = ?)); 
                """ # Adicionada verificação de segurança para que o cliente só veja seus pedidos
                
                # Para pegar o CPF do cliente logado para a query
                cpf_cliente_logado_data = db_connection.execute_query(conn, "SELECT CPF FROM Cliente WHERE Codigo_Pessoa = ?", (person_code,), fetch_results=True)
                cpf_cliente_logado = cpf_cliente_logado_data[0][0] if cpf_cliente_logado_data and cpf_cliente_logado_data[0][0] else None

                pedido = db_connection.execute_query(conn, sql_rastreio, (cod_rastreio, person_code, person_code, person_code if cpf_cliente_logado else -1 ), fetch_results=True) # -1 se não tiver CPF para não dar match errado
                
                if pedido:
                    p_data = pedido[0]
                    print("\n--- Detalhes do Pedido ---")
                    print(f"Produto ID: {p_data[0]}")
                    print(f"Status Atual: {p_data[1]}")
                    print(f"Tipo: {p_data[2]}")
                    print(f"Chegada no CD: {p_data[3] or 'N/A'}")
                    print(f"Previsão de Entrega: {p_data[4] or 'N/A'}")
                    print(f"Remetente: {p_data[5]}")
                    print(f"Destinatário (Rastreio): {p_data[6]}")
                    if p_data[7]: # Se tiver motorista
                        print(f"Motorista: {p_data[7]} (Veículo: {p_data[8] or 'N/A'} - {p_data[9] or 'N/A'})")
                    # Aqui poderia adicionar um histórico de status se a tabela existisse
                else:
                    print("Pedido não encontrado ou você não tem permissão para visualizá-lo.")
            press_enter_to_continue()

        elif choice == 2:
            list_products_terminal(conn, for_client_person_code=person_code)
            press_enter_to_continue()

        elif choice == 3: # Ver/Atualizar Dados Pessoais (Pessoa e Cliente)
            print("\n--- Meus Dados Pessoais (Pessoa) ---")
            # Mostra dados da Pessoa
            sql_pessoa = "SELECT Nome, RG, Telefone, Email FROM Pessoa WHERE Codigo_Pessoa = ?"
            dados_pessoa = db_connection.execute_query(conn, sql_pessoa, (person_code,), fetch_results=True)
            if dados_pessoa:
                dp = dados_pessoa[0]
                print(f"Nome: {dp[0]}\nRG: {dp[1] or ''}\nTelefone: {dp[2]}\nEmail: {dp[3]}")
            if input("Deseja atualizar os dados da Pessoa? (s/n): ").lower() == 's':
                update_person_terminal(conn) # A função já pede o ID, mas idealmente passaria person_code

            print("\n--- Meus Dados de Cliente (PF/PJ) ---")
            # Mostra dados do Cliente
            sql_cliente_data = """
            SELECT Tipo_Cliente, CPF, FORMAT(Data_Nascimento, 'dd/MM/yyyy'), CNPJ, Nome_Empresa
            FROM Cliente WHERE Codigo_Pessoa = ?
            """
            dados_cli = db_connection.execute_query(conn, sql_cliente_data, (person_code,), fetch_results=True)
            if dados_cli:
                dc = dados_cli[0]
                print(f"Tipo: {dc[0]}")
                if dc[0] == 'PF':
                    print(f"CPF: {dc[1] or ''}\nData de Nascimento: {dc[2] or ''}")
                else:
                    print(f"CNPJ: {dc[3] or ''}\nNome da Empresa: {dc[4] or ''}")
            if input("Deseja atualizar os dados de Cliente (PF/PJ)? (s/n): ").lower() == 's':
                update_client_terminal(conn, person_code_logged_in=person_code)
            press_enter_to_continue()

        elif choice == 4: # Ver/Atualizar Endereços
            print("\n--- Meus Endereços ---")
            # Um cliente pode ter múltiplos endereços, mas o script SQL atual associa apenas um ID_Endereco à Pessoa.
            # Para múltiplos endereços, seria necessária uma tabela associativa Pessoa_Endereco.
            # Por ora, mostramos o endereço principal.
            sql_endereco = """
            SELECT E.ID_Endereco, E.CEP, E.Rua, E.Numero, E.Complemento, E.Bairro, E.Cidade, E.Estado
            FROM Pessoa P JOIN Endereco E ON P.ID_Endereco = E.ID_Endereco
            WHERE P.Codigo_Pessoa = ?
            """
            end_data = db_connection.execute_query(conn, sql_endereco, (person_code,), fetch_results=True)
            if end_data:
                ed = end_data[0]
                print(f"Endereço Principal (ID: {ed[0]}):")
                print(f"  {ed[2]}, {ed[3]} {ed[4] or ''} - Bairro: {ed[5]}")
                print(f"  {ed[6]} - {ed[7]}, CEP: {ed[1]}")
                
                if input("Deseja atualizar este endereço? (s/n): ").lower() == 's':
                    # A função update_person_terminal atualiza o endereço principal.
                    # Seria preciso uma função específica para só atualizar o endereço se não quiser mexer nos dados da pessoa.
                    print("A atualização do endereço principal é feita através da atualização dos dados da Pessoa.")
                    update_person_terminal(conn) # Re-pede o ID, idealmente passaria person_code
            else:
                print("Nenhum endereço principal encontrado.")
            press_enter_to_continue()

        elif choice == 0:
            break

def menu_admin(conn, user_login, person_code):
    admin_options = [
        "Gerenciar Usuários", "Gerenciar Pessoas", "Gerenciar Clientes", "Gerenciar Funcionários",
        "Gerenciar Veículos", "Gerenciar Sedes", "Gerenciar Produtos a Entregar",
        "Gerenciar Dados de Rastreamento", "Gerenciar Carregamentos"
    ]
    while True:
        clear_screen()
        choice = display_menu(f"Menu Principal do Administrador - {user_login}", admin_options)

        if choice == 1: manage_users_terminal(conn)
        elif choice == 2: manage_people_terminal(conn)
        elif choice == 3: manage_clients_terminal(conn)
        elif choice == 4: manage_employees_terminal(conn)
        elif choice == 5: manage_vehicles_terminal(conn)
        elif choice == 6: manage_headquarters_terminal(conn)
        elif choice == 7: manage_products_terminal(conn)
        elif choice == 8: manage_tracking_terminal(conn)
        elif choice == 9: manage_shipments_terminal(conn)
        elif choice == 0:
            break # Sai do menu do admin, volta para a tela de login/inicial

# Placeholder para outros menus de funcionários
def menu_gerente(conn, user_login, person_code):
    print(f"\n--- Menu do Gerente: {user_login} (Cód. Pessoa: {person_code}) ---")
    print("Funcionalidades do Gerente a serem implementadas:")
    print("- Visualizar/Gerenciar Funcionários da Sede")
    print("- Visualizar/Gerenciar Veículos (da Sede ou todos)")
    print("- Visualizar Produtos na Sede")
    print("- Aprovar/Iniciar Carregamentos")
    print("- Gerar Relatórios (Entregas, Desempenho, etc.)")
    press_enter_to_continue()

def menu_atendente(conn, user_login, person_code):
    print(f"\n--- Menu do Atendente: {user_login} (Cód. Pessoa: {person_code}) ---")
    print("Funcionalidades do Atendente a serem implementadas:")
    print("- Cadastrar Novos Pedidos (Produtos a Serem Entregues)")
    print("- Consultar Status de Pedidos para Clientes")
    print("- Registrar Ocorrências/Solicitações de Clientes")
    print("- Interagir com Clientes (Telefone, Email - simulado)")
    press_enter_to_continue()

def menu_motorista(conn, user_login, person_code):
    print(f"\n--- Menu do Motorista: {user_login} (Cód. Pessoa: {person_code}) ---")
    # Obter placa do veículo do motorista
    motorista_data = db_connection.execute_query(conn, "SELECT Placa_Veiculo FROM Funcionario WHERE Codigo_Funcionario = ?", (person_code,), fetch_results=True)
    placa_veiculo_motorista = motorista_data[0][0] if motorista_data and motorista_data[0][0] else "N/A"
    print(f"Veículo associado: {placa_veiculo_motorista}")

    print("\nFuncionalidades do Motorista a serem implementadas:")
    print("- Visualizar Entregas Atribuídas")
    print("- Atualizar Status da Entrega (Ex: 'Em trânsito para entrega', 'Entregue', 'Tentativa falhou')")
    print("- Registrar Comprovante de Entrega (simplificado)")
    print("- Visualizar Rota (simulado)")
    print("- Registrar Ocorrências na Rota")
    press_enter_to_continue()

def menu_auxiliar_logistica(conn, user_login, person_code):
    print(f"\n--- Menu do Auxiliar de Logística: {user_login} (Cód. Pessoa: {person_code}) ---")
    # Obter sede do auxiliar
    aux_data = db_connection.execute_query(conn, "SELECT ID_Sede FROM Funcionario WHERE Codigo_Funcionario = ?", (person_code,), fetch_results=True)
    id_sede_aux = aux_data[0][0] if aux_data and aux_data[0][0] else "N/A"
    print(f"Sede associada: {id_sede_aux}")

    print("\nFuncionalidades do Auxiliar de Logística a serem implementadas:")
    print("- Registrar Chegada de Produtos na Sede/CD")
    print("- Organizar Produtos para Carregamento")
    print("- Atribuir Produtos a Veículos/Carregamentos (em conjunto com Gerente/Sistema)")
    print("- Atualizar Status de Produtos na Sede (Localização Interna, etc.)")
    print("- Gerenciar Estoque na Sede (simplificado)")
    press_enter_to_continue()

# ------------------- TELA DE LOGIN ----------------------
def login_tela(conn):
    logged_in_user = None
    user_type = None
    user_person_code = None
    
    while True:
        clear_screen()
        print("--- Tela de Login ---")
        username = input("Login: ").strip()
        password = getpass.getpass("Senha: ").strip()
        
        if not username or not password:
            print("Por favor, preencha usuário e senha.")
            press_enter_to_continue()
            continue
        
        sql = "SELECT Senha_Hash, Tipo_Usuario, Codigo_Pessoa FROM Usuario WHERE Login = ?"
        user_data = db_connection.execute_query(conn, sql, (username,), fetch_results=True)

        if user_data:
            stored_hash, retrieved_user_type, retrieve_person_code = user_data[0]
            if verify_password(stored_hash, password):
                logged_in_user = username
                user_type = retrieved_user_type
                user_person_code = retrieve_person_code # Este é o Codigo_Pessoa
                print(f"Login bem-sucedido! Bem-vindo, {logged_in_user} ({user_type}).")
                press_enter_to_continue()
                break # Sai do loop de login
            else:
                print("Usuário ou senha inválidos. Tente novamente.")
        else:
            print("Usuário não encontrado. Tente novamente.")
        press_enter_to_continue()

    # Direcionamento pós-login
    if logged_in_user:
        if user_type == 'Admin':
            menu_admin(conn, logged_in_user, user_person_code)
        elif user_type == 'Cliente':
            menu_cliente(conn, logged_in_user, user_person_code)
        elif user_type == 'Gerente':
            menu_gerente(conn, logged_in_user, user_person_code)
        elif user_type == 'Atendente':
            menu_atendente(conn, logged_in_user, user_person_code)
        elif user_type == 'Motorista':
            menu_motorista(conn, logged_in_user, user_person_code)
        elif user_type == 'Auxiliar de Logistica': # Corrigido para corresponder ao BD
            menu_auxiliar_logistica(conn, logged_in_user, user_person_code)
        else:
            print(f"Tipo de usuário '{user_type}' não possui um menu definido. Contate o administrador.")
            press_enter_to_continue()


# ------------------- MENU INICIAL ----------------------
def menu_inicial_principal(): # Renomeado para evitar conflito
    options = ["Fazer Login", "Cadastrar-se como Cliente"]
    while True:
        clear_screen()
        choice = display_menu("Bem-vindo ao Sistema de Rastreamento e Logística", options)
        if choice == 1:
            return 'login'
        elif choice == 2:
            return 'cadastro_cliente'
        elif choice == 0:
            print("Saindo do sistema...")
            return 'sair' # Retorna 'sair' para o loop principal da aplicação


# ------------------- RODAR APLICAÇÃO ----------------------
def run_app_terminal():
    conn = db_connection.conectar_banco()
    try:
        if not conn:
            print("Erro crítico: Não foi possível conectar ao banco de dados.")
            print("Verifique as configurações em db_connection.py, o driver ODBC e a acessibilidade do servidor Azure SQL.")
            return

        while True:
            acao = menu_inicial_principal()
            if acao == 'cadastro_cliente':
                cadastro_cliente_self_service(conn)
                press_enter_to_continue()
            elif acao == 'login':
                login_tela(conn) # login_tela agora gerencia o loop do menu do usuário logado
                # Quando login_tela retorna, significa que o usuário fez logout ou saiu do seu menu específico.
                # O loop while True em run_app_terminal trará de volta ao menu_inicial_principal.
            elif acao == 'sair':
                break # Sai do loop principal da aplicação

    except KeyboardInterrupt:
        print("\nOperação cancelada pelo usuário. Saindo.")
    except Exception as e:
        print(f"Ocorreu um erro inesperado na aplicação: {e}")
        import traceback
        traceback.print_exc() # Imprime o stack trace para depuração
    finally:
        if conn:
            db_connection.desconectar_banco(conn)
            print("Conexão com o banco de dados fechada.")

if __name__ == "__main__":
    run_app_terminal()
