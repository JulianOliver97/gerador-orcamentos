document.addEventListener("DOMContentLoaded", () => {

    // =====================================================
    // ELEMENTOS PRINCIPAIS
    // =====================================================

    const formulario =
        document.getElementById("form-orcamento");

    const inputLogo =
        document.getElementById("logo");

    const logoBase64 =
        document.getElementById("logo_base64");

    const previewLogo =
        document.getElementById("preview-logo");

    const botaoAdicionarServico =
        document.getElementById("adicionar-servico");

    const listaServicos =
        document.getElementById("lista-servicos");

    const botaoLimpar =
        document.getElementById("limpar-orcamento");

    const documentoCliente =
        document.getElementById("documento_cliente");

    const cnpjEmpresa =
        document.getElementById("cnpj_empresa");

    const telefone =
        document.getElementById("telefone");

    const campoValor =
        document.getElementById("valor");

    const campoEmpresa =
        document.getElementById("empresa");

    const campoEnderecoEmpresa =
        document.getElementById("endereco_empresa");


    // =====================================================
    // CHAVES DO LOCALSTORAGE
    // =====================================================

    const CHAVE_EMPRESA =
        "geradorOrcamentos_empresa";

    const CHAVE_CNPJ =
        "geradorOrcamentos_cnpj";

    const CHAVE_ENDERECO =
        "geradorOrcamentos_endereco";

    const CHAVE_TELEFONE =
        "geradorOrcamentos_telefone";

    const CHAVE_LOGO =
        "geradorOrcamentos_logo";


    // =====================================================
    // SALVAR DADOS DA EMPRESA
    // =====================================================

    function salvarDadosEmpresa() {

        localStorage.setItem(
            CHAVE_EMPRESA,
            campoEmpresa.value
        );

        localStorage.setItem(
            CHAVE_CNPJ,
            cnpjEmpresa.value
        );

        localStorage.setItem(
            CHAVE_ENDERECO,
            campoEnderecoEmpresa.value
        );

        localStorage.setItem(
            CHAVE_TELEFONE,
            telefone.value
        );
    }


    // =====================================================
    // CARREGAR DADOS DA EMPRESA
    // =====================================================

    function carregarDadosEmpresa() {

        campoEmpresa.value =
            localStorage.getItem(
                CHAVE_EMPRESA
            ) || "";

        cnpjEmpresa.value =
            localStorage.getItem(
                CHAVE_CNPJ
            ) || "";

        campoEnderecoEmpresa.value =
            localStorage.getItem(
                CHAVE_ENDERECO
            ) || "";

        telefone.value =
            localStorage.getItem(
                CHAVE_TELEFONE
            ) || "";


        const logoSalva =
            localStorage.getItem(
                CHAVE_LOGO
            );


        if (logoSalva) {

            logoBase64.value =
                logoSalva;

            previewLogo.innerHTML = `
                <img
                    src="${logoSalva}"
                    alt="Logo da empresa"
                >
            `;

        } else {

            logoBase64.value = "";

            previewLogo.innerHTML =
                "Nenhuma logo selecionada";
        }
    }


    // =====================================================
    // SALVAR AUTOMATICAMENTE EMPRESA
    // =====================================================

    campoEmpresa.addEventListener(
        "input",
        salvarDadosEmpresa
    );

    cnpjEmpresa.addEventListener(
        "input",
        salvarDadosEmpresa
    );

    campoEnderecoEmpresa.addEventListener(
        "input",
        salvarDadosEmpresa
    );

    telefone.addEventListener(
        "input",
        salvarDadosEmpresa
    );


    // =====================================================
    // LOGO
    // =====================================================

    inputLogo.addEventListener(
        "change",
        function () {

            const arquivo =
                this.files[0];


            if (!arquivo) {

                return;
            }


            if (
                !arquivo.type.startsWith(
                    "image/"
                )
            ) {

                alert(
                    "Selecione um arquivo de imagem válido."
                );

                this.value = "";

                return;
            }


            // Evita armazenar imagens enormes
            // no navegador.

            const limite =
                2 * 1024 * 1024;


            if (arquivo.size > limite) {

                alert(
                    "A logo deve ter no máximo 2 MB."
                );

                this.value = "";

                return;
            }


            const leitor =
                new FileReader();


            leitor.onload = function (evento) {

                const imagem =
                    evento.target.result;


                previewLogo.innerHTML = `
                    <img
                        src="${imagem}"
                        alt="Logo da empresa"
                    >
                `;


                logoBase64.value =
                    imagem;


                try {

                    localStorage.setItem(
                        CHAVE_LOGO,
                        imagem
                    );

                } catch (erro) {

                    console.error(
                        "Não foi possível salvar a logo:",
                        erro
                    );

                    alert(
                        "A logo foi carregada, mas não pôde ser salva no navegador."
                    );
                }
            };


            leitor.readAsDataURL(
                arquivo
            );
        }
    );


    // =====================================================
    // CRIAR SERVIÇO
    // =====================================================

    function criarNovoServico() {

        const novoServico =
            document.createElement(
                "div"
            );


        novoServico.classList.add(
            "servico"
        );


        novoServico.innerHTML = `

            <div class="conteudo-servico">

                <input
                    type="text"
                    name="titulos_servicos[]"
                    placeholder="Título do serviço"
                    class="titulo-servico"
                    required
                >

                <textarea
                    name="descricoes_servicos[]"
                    placeholder="Descreva detalhadamente o serviço que será realizado..."
                    required
                ></textarea>

            </div>

            <button
                type="button"
                class="remover-servico"
            >
                Remover
            </button>

        `;


        listaServicos.appendChild(
            novoServico
        );


        novoServico
            .querySelector(
                ".titulo-servico"
            )
            .focus();
    }


    // =====================================================
    // ADICIONAR SERVIÇO
    // =====================================================

    botaoAdicionarServico.addEventListener(
        "click",
        criarNovoServico
    );


    // =====================================================
    // REMOVER SERVIÇO
    // =====================================================

    listaServicos.addEventListener(
        "click",
        function (evento) {

            if (
                !evento.target.classList.contains(
                    "remover-servico"
                )
            ) {

                return;
            }


            const servicos =
                listaServicos.querySelectorAll(
                    ".servico"
                );


            if (servicos.length === 1) {

                alert(
                    "O orçamento precisa ter pelo menos um serviço."
                );

                return;
            }


            evento.target
                .closest(".servico")
                .remove();
        }
    );


    // =====================================================
    // CPF / CNPJ DO CLIENTE
    // =====================================================

    function formatarDocumento(valor) {

        valor =
            valor.replace(
                /\D/g,
                ""
            );


        // CPF

        if (valor.length <= 11) {

            valor =
                valor.slice(
                    0,
                    11
                );


            return valor
                .replace(
                    /(\d{3})(\d)/,
                    "$1.$2"
                )
                .replace(
                    /(\d{3})(\d)/,
                    "$1.$2"
                )
                .replace(
                    /(\d{3})(\d{1,2})$/,
                    "$1-$2"
                );
        }


        // CNPJ

        valor =
            valor.slice(
                0,
                14
            );


        return valor
            .replace(
                /^(\d{2})(\d)/,
                "$1.$2"
            )
            .replace(
                /^(\d{2})\.(\d{3})(\d)/,
                "$1.$2.$3"
            )
            .replace(
                /\.(\d{3})(\d)/,
                ".$1/$2"
            )
            .replace(
                /(\d{4})(\d)/,
                "$1-$2"
            );
    }


    documentoCliente.addEventListener(
        "input",
        function () {

            this.value =
                formatarDocumento(
                    this.value
                );
        }
    );


    // =====================================================
    // CNPJ DA EMPRESA
    // =====================================================

    cnpjEmpresa.addEventListener(
        "input",
        function () {

            let valor =
                this.value.replace(
                    /\D/g,
                    ""
                );


            valor =
                valor.slice(
                    0,
                    14
                );


            valor = valor
                .replace(
                    /^(\d{2})(\d)/,
                    "$1.$2"
                )
                .replace(
                    /^(\d{2})\.(\d{3})(\d)/,
                    "$1.$2.$3"
                )
                .replace(
                    /\.(\d{3})(\d)/,
                    ".$1/$2"
                )
                .replace(
                    /(\d{4})(\d)/,
                    "$1-$2"
                );


            this.value = valor;


            salvarDadosEmpresa();
        }
    );


    // =====================================================
    // TELEFONE
    // =====================================================

    telefone.addEventListener(
        "input",
        function () {

            let valor =
                this.value.replace(
                    /\D/g,
                    ""
                );


            valor =
                valor.slice(
                    0,
                    11
                );


            if (valor.length <= 10) {

                valor = valor
                    .replace(
                        /^(\d{2})(\d)/,
                        "($1) $2"
                    )
                    .replace(
                        /(\d{4})(\d)/,
                        "$1-$2"
                    );

            } else {

                valor = valor
                    .replace(
                        /^(\d{2})(\d)/,
                        "($1) $2"
                    )
                    .replace(
                        /(\d{5})(\d)/,
                        "$1-$2"
                    );
            }


            this.value = valor;


            salvarDadosEmpresa();
        }
    );


    // =====================================================
    // VALOR EM REAL
    // =====================================================

    campoValor.addEventListener(
        "input",
        function () {

            let valor =
                this.value.replace(
                    /\D/g,
                    ""
                );


            if (!valor) {

                this.value = "";

                return;
            }


            const numero =
                Number(valor) / 100;


            this.value =
                numero.toLocaleString(
                    "pt-BR",
                    {
                        style: "currency",
                        currency: "BRL"
                    }
                );
        }
    );


    // =====================================================
    // LIMPAR SOMENTE O ORÇAMENTO
    // =====================================================

    botaoLimpar.addEventListener(
        "click",
        function () {

            const confirmar =
                confirm(
                    "Deseja limpar os dados deste orçamento? Os dados da empresa serão mantidos."
                );


            if (!confirmar) {

                return;
            }


            // Cliente

            document.getElementById(
                "cliente"
            ).value = "";

            documentoCliente.value = "";

            document.getElementById(
                "endereco_cliente"
            ).value = "";


            // Valores e condições

            campoValor.value = "";

            document.getElementById(
                "validade"
            ).value = "";

            document.getElementById(
                "forma_pagamento"
            ).value = "";

            document.getElementById(
                "prazo_execucao"
            ).value = "";

            document.getElementById(
                "observacoes"
            ).value = "";


            // Remove todos os serviços.

            listaServicos.innerHTML = "";


            // Cria um serviço vazio novamente.

            criarNovoServico();


            // Leva para o cliente.

            document.getElementById(
                "cliente"
            ).focus();
        }
    );


    // =====================================================
    // BOTÃO GERAR PDF
    // =====================================================

    formulario.addEventListener(
        "submit",
        function () {

            salvarDadosEmpresa();


            const botaoGerar =
                formulario.querySelector(
                    ".btn-principal"
                );


            botaoGerar.innerText =
                "Gerando PDF...";


            botaoGerar.disabled =
                true;


            setTimeout(
                () => {

                    botaoGerar.innerText =
                        "Gerar Orçamento PDF";

                    botaoGerar.disabled =
                        false;

                },
                4000
            );
        }
    );


    // =====================================================
    // CARREGAMENTO INICIAL
    // =====================================================

    carregarDadosEmpresa();

});