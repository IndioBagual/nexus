import os
import sys
import unittest


def run_nexus_tests():
    # 1. Garante que a raiz do projeto está no PATH
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)

    print("🚀 Iniciando Testes do NEXUS LIFE OS")
    print(f"📂 Diretório: {current_dir}")
    print("-" * 40)

    # 2. Descobre e executa os testes dentro da pasta 'tests'
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir="tests", pattern="test_*.py")

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 3. Resumo para o desenvolvedor
    if result.wasSuccessful():
        print("\n✨ Todos os testes passaram! O Kernel está estável.")
        sys.exit(0)
    else:
        print("\n❌ Alguns testes falharam. Verifique os logs acima.")
        sys.exit(1)


if __name__ == "__main__":
    run_nexus_tests()
