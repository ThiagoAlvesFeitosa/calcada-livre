from app.config import nomes_variaveis_faltando


def test_variaveis_supabase_faltando_citam_o_nome_sem_o_valor() -> None:
    # preparar
    ambiente = {"ARMAZENAMENTO": "supabase", "SUPABASE_URL": "https://exemplo.supabase.co"}

    # executar
    faltando = nomes_variaveis_faltando("supabase", ambiente)
    texto = "Faltam variáveis: " + ", ".join(faltando)

    # verificar
    assert "SUPABASE_KEY" in faltando
    assert "SUPABASE_BUCKET" in faltando
    assert "SUPABASE_URL" not in faltando
    assert "https://exemplo.supabase.co" not in texto


def test_armazenamento_local_nao_exige_chaves_supabase() -> None:
    # preparar
    ambiente = {"ARMAZENAMENTO": "local"}

    # executar
    faltando = nomes_variaveis_faltando("local", ambiente)

    # verificar
    assert faltando == []
