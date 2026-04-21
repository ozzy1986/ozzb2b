<?php
error_reporting( E_ALL );
ini_set( 'display_errors', 1 );

$telegram_bot_token = '908186694:AAF6Q5hkbla0PvdaU87X8UuY25ycrNnYl_c';

// setting webhook. needs to run only once
/*
$webhook_url	= 'https://api.telegram.org/bot' . $telegram_bot_token . '/setWebhook?url=https://' . $_SERVER['HTTP_HOST'] . $_SERVER['REQUEST_URI'];
$webhook		= file_get_contents( $webhook_url );
echo '<br>$webhook_url:<pre>' . print_r( $webhook_url, true ) . '</pre>';
echo '<br>$webhook:<pre>' . print_r( $webhook, true ) . '</pre>';
*/


require 'vendor/autoload.php';

try {
    $bot = new \TelegramBot\Api\Client( $telegram_bot_token ); 


    // команда для start
	$bot->command( 'start', function ( $message ) use ( $bot ) {
		$answer = 'Добро пожаловать!';
		$bot->sendMessage( $message->getChat()->getId(), $answer );
	});

	// команда для помощи
	$bot->command( 'help', function ( $message ) use ( $bot ) {
		$answer = 'Команды:
	/help - вывод справки';
		$bot->sendMessage( $message->getChat()->getId(), $answer );
	});

	
	$bot->command( 'hello', function ( $message ) use ( $bot ) {
		$text	= $message->getText();
		$param	= str_replace( '/hello ', '', $text );
		$answer	= 'Неизвестная команда';
		if ( !empty( $param ) ) {
			$answer = 'Привет, ' . $param;
		}
		$bot->sendMessage( $message->getChat()->getId(), $answer );
	});



    $bot->run();

} catch ( \TelegramBot\Api\Exception $e ) {
    $e->getMessage();
}


function main() {
	$telegram = new Telegram();
	// подключаем хранилище
	$storage = new Storage();
	// получаем объект сообщения
	$message = $telegram->getMessage();
	// получаем команду, если ее передали
	$command = $message->getCommand();
	// получаем текст, если его передали (тут лежит все, что не является командой)
	$text = $message->getParams( $command );
	// если команда пустая, то мы проверяем, есть ли у пользователя на предыдущем шаге вызов команды и восстановливаем ее
	if ( empty( $command ) ) {
	  $command = $storage->restoreCommand( $message->getChat()->getId() );
	}
	// запоминаем команду, котрую ввел пользователь
	$storage->storeCommand(
	    $message->getChat()->getId(),
	    $command
	);
	// логика подключения нашего метода для котроллера
	$this->chooseMethod( $command, $message, $text );
}

function getnewtext( $message $telegram, $text ) {
	// если не передали текст, то выведем сообщение с разъяснением
	if ( empty( $text ) ) {
		$answer = 'Введите слово или несколько слов для поиска. Именно по ним будет происходить поиск 5 свежих новостей.';
		$telegram->sendMessage( $telegram->getChat()->getId(), $answer );
	} else {
		// основаня логика
		$tg_news = new TelegramNews();
		$ar_data = $tg_news->getByWord( $text, 'new' );
		if ( empty( $ar_data ) ) {
			$answer = 'Ничего не найдено';
		} else {
			$answer = common_setViewGetContent( 'telegram/get', [
				'data' => $ar_data
			]);
		}
		$telegram->sendMessage( $telegram->getChat()->getId(), $answer );
	}
}
