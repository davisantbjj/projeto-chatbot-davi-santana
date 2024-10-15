from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from twilio.twiml.messaging_response import MessagingResponse
from .models import Userresponse  # Importando o modelo correto
import time

# Lista de perguntas do quiz e opções válidas
anamnese_questions = [
    {
        "question": "1. Qual o seu nível de inglês? \n(a/b/c)\n"
                    "a. Tenho pouco conhecimento da língua (vocabulário e gramática) e não falo nada. Socorro! 🌟\n"
                    "b. Tenho um bom conhecimento da língua (vocabulário e gramática), mas falo com dificuldade. Preciso de ajuda! 🙏\n"
                    "c. Tenho um ótimo conhecimento da língua (vocabulário e gramática), mas não pratico há um tempo. Me dá uma forcinha! 💪",
        "valid_answers": ['a', 'b', 'c']
    },
    {
        "question": "2. A sua experiência anterior com o aprendizado de idiomas foi: \n(a/b/c)\n"
                    "a. Apenas em escolas; com músicas, filmes e séries 🎶\n"
                    "b. No trabalho 💼\n"
                    "c. Em viagens ✈️",
        "valid_answers": ['a', 'b', 'c']
    },
    {
        "question": "3. O que te motivou a aprender inglês? \n(a/b/c)\n"
                    "a. Preciso aprender a me comunicar em qualquer situação do dia a dia 🗣️\n"
                    "b. Preciso utilizar no meu trabalho 🏢\n"
                    "c. Preciso para viajar 🌍",
        "valid_answers": ['a', 'b', 'c']
    },
    {
        "question": "4. Quanto tempo você pode dedicar ao estudo do inglês por semana? \n(a/b/c)\n"
                    "a. 01 vez na semana – 01 hora por dia ⏰\n"
                    "b. 02 vezes na semana – 01 hora por dia ⏰\n"
                    "c. Todos os dias – 01 hora por dia ⏰",
        "valid_answers": ['a', 'b', 'c']
    },
    {
        "question": "5. Quais métodos de aprendizagem você tentou no passado? \n(a/b/c/d)\n"
                    "a. Estudo Autodidata ( ) Funcionou ( ) Não funcionou\n"
                    "b. Aulas Formais ( ) Funcionou ( ) Não funcionou\n"
                    "c. Imersão Cultural ( ) Funcionou ( ) Não funcionou\n"
                    "d. Conversação Prática ( ) Funcionou ( ) Não funcionou",
        "valid_answers": ['a', 'b', 'c', 'd']
    },
    {
        "question": "6. Você tem alguma dificuldade específica no aprendizado do inglês? \n(a/b/c/d/e)\n"
                    "a. Pronúncia 🗣️\n"
                    "b. Gramática 📚\n"
                    "c. Vocabulário 📝\n"
                    "d. Compreensão Auditiva 🎧\n"
                    "e. Confiança na Conversação 💬",
        "valid_answers": ['a', 'b', 'c', 'd', 'e']
    },
]

# Dicionário para rastrear o progresso de cada usuário
current_anamnese_index = {}
user_registration = {}  # Rastreamento do processo de registro do usuário

@csrf_exempt
def receive_message(request):
    if request.method == 'POST':
        from_number = request.POST.get('From')
        incoming_message = request.POST.get('Body', '').strip().lower()

        # Verifica se o usuário já está cadastrado
        user = Userresponse.objects.filter(phone_number=from_number).first()

        # Se o usuário já está cadastrado, pergunta se quer responder à anamnese novamente
        if user:
            if from_number not in current_anamnese_index:
                response = MessagingResponse()
                response.message("Você já está cadastrado! Gostaria de responder à anamnese novamente? (responda 'sim' ou 'não')")
                current_anamnese_index[from_number] = -1  # Define o estado para esperar a resposta
                return HttpResponse(str(response))

            if current_anamnese_index[from_number] == -1:
                # Usuário responde se quer refazer a anamnese
                if incoming_message == 'sim':
                    response = MessagingResponse()
                    response.message("Ok, vamos reiniciar a anamnese.")
                    current_anamnese_index[from_number] = 0  # Reinicia o índice da anamnese
                    response.message(anamnese_questions[0]["question"])
                    return HttpResponse(str(response))
                elif incoming_message == 'não':
                    response = MessagingResponse()
                    response.message("Tudo bem! Se precisar de algo, estou por aqui.")
                    del current_anamnese_index[from_number]  # Reseta a sessão do usuário
                    return HttpResponse(str(response))
                else:
                    response = MessagingResponse()
                    response.message("Por favor, responda com 'sim' ou 'não'.")
                    return HttpResponse(str(response))

        # Caso o usuário não esteja cadastrado, continuar o processo de cadastro
        if not user:
            if from_number not in user_registration:
                user_registration[from_number] = {"step": 0, "data": {}}

            registration_step = user_registration[from_number]["step"]

            if registration_step == 0:
                response = MessagingResponse()
                response.message("Bem-vindo! Antes de começarmos, por favor, informe seu nome completo:")
                user_registration[from_number]["step"] += 1
                return HttpResponse(str(response))

            elif registration_step == 1:
                user_registration[from_number]["data"]["name"] = incoming_message
                response = MessagingResponse()
                response.message("Agora, por favor, informe seu CPF (somente números):")
                user_registration[from_number]["step"] += 1
                return HttpResponse(str(response))

            elif registration_step == 2:
                user_registration[from_number]["data"]["cpf"] = incoming_message
                response = MessagingResponse()
                response.message("Informe seu email:")
                user_registration[from_number]["step"] += 1
                return HttpResponse(str(response))

            elif registration_step == 3:
                user_registration[from_number]["data"]["email"] = incoming_message
                user_data = user_registration[from_number]["data"]

                # Salva o novo usuário no banco de dados
                new_user = Userresponse.objects.create(
                    phone_number=from_number,
                    name=user_data["name"],
                    cpf=user_data["cpf"],
                    email=user_data["email"],
                    responses=""  # Inicializa com vazio
                )
                new_user.save()

                del user_registration[from_number]  # Limpa o processo de registro

                # Após o cadastro, inicia a anamnese
                response = MessagingResponse()
                response.message("Cadastro concluído! Agora vamos iniciar a anamnese.")
                time.sleep(2)
                current_anamnese_index[from_number] = 0  # Inicializa o índice de anamnese
                response.message(anamnese_questions[0]["question"])
                return HttpResponse(str(response))

        # Se o usuário está respondendo ao questionário
        question_idx = current_anamnese_index.get(from_number, 0)
        if question_idx < len(anamnese_questions):
            valid_answers = anamnese_questions[question_idx]["valid_answers"]
            if incoming_message in valid_answers:
                # Salva a resposta
                user.responses = (user.responses or "") + f"{anamnese_questions[question_idx]['question']} {incoming_message}\n"
                user.save()

                current_anamnese_index[from_number] += 1

                if current_anamnese_index[from_number] < len(anamnese_questions):
                    # Pergunta a próxima questão
                    response = MessagingResponse()
                    response.message(anamnese_questions[current_anamnese_index[from_number]]["question"])
                    return HttpResponse(str(response))
                else:
                    # Finaliza o questionário
                    response = MessagingResponse()
                    response.message("Obrigado por responder à anamnese! Suas respostas foram registradas.")
                    del current_anamnese_index[from_number]
                    return HttpResponse(str(response))
            else:
                # Solicitar novamente a mesma pergunta
                response = MessagingResponse()
                response.message(f"Resposta inválida. Por favor, responda com {', '.join(valid_answers)}.")
                return HttpResponse(str(response))

    return JsonResponse({"error": "Método não permitido"}, status=405)
