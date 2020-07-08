### Busca de registro de pedidos na api neemo

<p>Para que o projeto seja executado corretamente é necessário ter o python instalado na maquina</p>
<p>Também é necessário ter virtualenv instalado para poder instalar as biblitecas python que serão usadas neste projeto</p>

#### Passos para rodar o projeto

- Primeiro certifique-se que está no <i>virtual enviroment</i> https://www.liquidweb.com/kb/how-to-setup-a-python-virtual-environment-on-windows-10/
- Instale as biblitecas necessárias com o comando `pip3 install -r requirements.txt`
- Renomeie o arquivo `.env-example` para `.env` e preencha as informações de token de acesso à api e local que o arquivo será salvo
- Após você pode rodar o sistema com o `python main.py`, este comando irá gerar os dados com base na data atual. 
Caso você queira a partir de uma data especifica você pode adicionar o parametro `--dt_ref YY-mm-ddd` por exemplo `python main.py --dt_ref 2020-07-07`
 
 <p>Se tudo ocorrer conforme esperado o arquivo será gerado na pasta informada no arquivo .env</p>