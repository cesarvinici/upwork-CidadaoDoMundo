import os
import requests
import json
import pandas as pd
import argparse
import time
from math import ceil
from datetime import datetime
from dotenv import load_dotenv
import dateutil.parser

load_dotenv()

parser = argparse.ArgumentParser()
parser.add_argument("--dt_ref", help="Data referência para busca dos dados: YYY-MM-DD")

args = parser.parse_args()

APP_URL = "https://deliveryapp.neemo.com.br/api/integration"
ORDERS = "/v1/order"
AGUA_VERDE_TOKEN = os.environ.get("AGUA_VERDE_TOKEN")
BOQUEIRAO_TOKEN = os.environ.get("BOQUEIRAO_TOKEN")
FILE_PATH = os.path.abspath(os.environ.get("FOLDER_PATH"))
ITEMS_PER_PAGE = 50
DT_REF = args.dt_ref if args.dt_ref else datetime.date(datetime.today())


def parse_data(orders: list, filial: str) -> list:
    """
    Insert 'order_id' and 'filial' into a list \n
    :param orders: list
    :param filial: str
    :return: parsed_orders: list
    """
    parsed_orders = []
    for order in orders:
        parsed_orders.append({"order_id": order['id'], "filial": filial})

    return parsed_orders


def map_order_status(status_id: int) -> str:
    status = {0: "Novo Pedido",
              1: "Confirmado",
              2: "Entregue",
              3: "Cancelado (restaurante)",
              4: "Enviado",
              5: "Cancelado Automaticamente (sistema)",
              6: "Cancelado com Pagamento Estornado (restaurante)",
              7: "Cancelado Automaticamente, com Pagamento Estornado"}
    return status[status_id]


def get_orders(tokens: dict) -> list:
    """
    Get all order_id of the given date
    :param tokens: dict
    :return: orders_list: list
    """
    orders_list = []
    for key in tokens:
        payload = {"token_account": tokens[key], "created_at": DT_REF, "limit": ITEMS_PER_PAGE}
        data = get_from_api(payload)
        orders = data['Orders']
        orders_list.extend(parse_data(orders, key))

        # checks if the total items is greater than limited items per page (50)
        # if so we need to grab the other pages
        if data['paging']['total'] > ITEMS_PER_PAGE:
            pages = ceil(data['paging']['total'] / ITEMS_PER_PAGE)
            for page in range(2, pages):
                payload['page'] = page
                data = get_from_api(payload)
                orders = data['Orders']
                orders_list.extend(parse_data(orders, key))

    return orders_list


def build_data(order: dict, item: dict, filial: str) -> dict:
    """
    Build the data that will be inserted into the csv file \n
    :param order: dict
    :param item: dict
    :param filial: str
    :return: dados: dict
    """
    if 'price_un' in item.keys():
        price = item['price_un']
    else:
        price = item['price']

    date = dateutil.parser.parse(order['date']).strftime("%d/%m/%Y %H:%M:%S")
    dados = {
        "Id_pedido": order['id'],
        "Data": date,
        "Item": item['title'],
        "Quantidade": item['quantity'],
        "Valor Unitario": price,
        "Subtotal": round(price * item['quantity'], 2),
        "Nome": order['name'].upper(),
        "Filial": filial.title(),
        "Canal": "SITE",
        "Pagamento": order['payment_method'].upper(),
        "Status": map_order_status(order['status'])
    }
    return dados


def get_order_items(orders: list, tokens: dict) -> list:
    """
    Get all orders itens given the order_id \n
    :param orders: list
    :param tokens: dict
    :return: registro_de_compra: list
    """
    registro_de_compra = []
    for order in orders:
        order_id = order['order_id']
        payload = {"token_account": tokens[order['filial']]}
        item_order = get_from_api(payload, order_id)['Order']
        for item in item_order['ItemOrder']:
            registro_de_compra.extend([build_data(item_order, item, order['filial'])])
            for complement in item['ComplementCategories']:
                for comp in complement['Complements']:
                    registro_de_compra.extend([build_data(item_order, comp, order['filial'])])
    return registro_de_compra


def get_from_api(payload: dict, order_id=None) -> json:
    """
    Connect to the API and retrive the data. \n
    :param payload:
    :param order_id:
    :return: json
    """
    try:
        if order_id:
            r = requests.post(f"{APP_URL}{ORDERS}/{order_id}", data=payload)
        else:
            r = requests.post(f"{APP_URL}{ORDERS}", data=payload)

        if r.status_code == 201:
            return json.loads(r.content)
        else:
            raise Exception(f"Oops, something went wrong: Status Code: {r.status_code}")
    except Exception:
        raise Exception("Something went wrong when calling the api.")


def extract_data(dados: list) -> None:
    """
    Extract data to .csv file. \n
    :param dados: list
    :return: None
    """
    data_frame = pd.DataFrame(dados)
    data_frame.to_csv(FILE_PATH + "/lista_vendas_" + str(DT_REF) + ".csv", encoding="utf-8-sig")


def main():
    start = time.time()
    tokens = {"agua verde": AGUA_VERDE_TOKEN, "boqueirao": BOQUEIRAO_TOKEN}

    print(str(datetime.today().strftime("%d/%m/%Y %H:%M:%S")) + " - BUSCANDO REGISTRO DE PEDIDOS...")
    orders = get_orders(tokens)

    print(str(datetime.today().strftime("%d/%m/%Y %H:%M:%S")) + " - BUSCANDO ITENS...")
    orders_data = get_order_items(orders, tokens)

    print(str(datetime.today().strftime("%d/%m/%Y %H:%M:%S")) + " - SALVANDO ARQUIVO...")
    extract_data(orders_data)

    print(str(datetime.today().strftime("%d/%m/%Y %H:%M:%S")) + " - DADOS CARREGADOS COM SUCESSO!")
    print(str(datetime.today().strftime("%d/%m/%Y %H:%M:%S")) + " - " + FILE_PATH + "/lista_vendas_" + str(DT_REF) + ".csv")

    print(str(datetime.today().strftime("%d/%m/%Y %H:%M:%S")) + " - Tempo total: " + str(round(time.time() - start, 2)) + " segundos")


if __name__ == "__main__":
    main()
