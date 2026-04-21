<?php

if ( !defined( 'ABSPATH' ) ) {
    exit;
}

class Telegram extends WC_Integration
{
   
	const API_TELEGRAM = 'https://api.telegram.org/bot';

    public $register_webhook;

    public $token;

    public $chat_id = array();

    public $user_id;

    public function __construct() {
    	$current_user	= wp_get_current_user();
        $this->user_id	= $current_user->ID;

        $this->id					= 'ozz-wc-telegram-bot';
        $this->method_title			= 'Телеграм бот для WooCommerce';
        $this->method_description	= 'Плагин связывает WooCommerce c Telegram ботом.';

        $this->init_form_fields();
        $this->init_settings();

        $this->settings['token']	= '1175394999:AAHBNeAYGR6fyIziPmlMfweu7MrkMZPlvP8';
        $this->token				= $this->settings['token'];
        $this->chat_id				= get_user_meta( $this->user_id, 'telegram', true );
        $this->register_webhook		= $this->check_exists_webhook( $this->token );

        add_action( 'woocommerce_update_options_integration_' . $this->id, array( $this, 'process_admin_options' ) );
        
        add_action( 'woocommerce_api_woo-telegram', array( $this, 'wc_telegram_response' ) );

        add_action( 'woocommerce_checkout_order_processed', array( $this, 'send_order_to_telegram' ), 10, 3 );

        if ( @$_GET['test'] == 'bot' ) {
        	//delete_user_meta( $this->user_id, 'telegram' );
        	//echo '<div style="position: absolute; background-color: white; z-index: 99999999999; width: 100%;"><pre>' . print_r( $this->get_telegram_users(), true ) . '</pre></div>';
        	echo '<div style="position: absolute; background-color: white; z-index: 99999999999; width: 100%;"><pre>' . print_r( $this->chat_id, true ) . '</pre></div>';
        }
    }

    public function init_form_fields() {
        $this->form_fields = [
            'token' => array(
                'title'       => __( 'Токен Telegram', 'woocommerce' ),
                'description' => __( 'Введите token полученный от BotFather', 'woocommerce' ),
                'type'        => 'text',
            	'class'       => 'tm-token',
                'desc_tip'    => true,
                'default'     => get_option( 'token' )
            ),
        ];
    }

	public function process_admin_options() {
        $result      = parent::process_admin_options();
        $this->token = $this->settings['token'];
        $this->set_telegram_webhook();
        $this->registerWebhook = $this->check_exists_webhook( $this->token );

        return $result;
    }

    public function admin_options()	 {
        $hash = md5( 'wctelegram2020' . $this->user_id );

        echo '<table class="form-table">';
        echo $this->generate_settings_html( $this->form_fields, false );
        echo '</table>';

        if ( !$this->register_webhook ) {
            echo '<div class="error warning" id="webhook">WebHook не зарегистрирован</div><br><br>';
        } else {

        
	        echo '<strong>Если Вы ещё не добавили себе бота:</strong><br>
	        	1. Найдите нашего бота @ozz_wc_telegram_bot<br>
	        	2. Нажмите "Начать"<br>
	        	3. Напишите команду "/key=' . $this->user_id . '&auth=' . $hash . '" дождитесь ответа бота и перегрузите эту страницу 
	        <br>';
	        
	        if ( !empty( $this->chat_id ) ) {
	        	$chat_id_list = implode( '<br>', $this->chat_id );
	            echo '<p>Номера активированных чатов для текущего пользователя:<br>' . $chat_id_list . '</p>';
	        }

	    }
        
        $this->display_errors();
    }

	public function wc_telegram_response() {
	    global $woocommerce;

	    $data   = file_get_contents( 'php://input' );
	    $logger = wc_get_logger();
	    
	    try {
	        $result				= $this->decode_post( $data );
	        $user_id			= $this->parse_text( $result['text'] );
	        
	        // add new chat_id to existing list
	        $current_chat_id	= array();
	        $current_chat_id	= get_user_meta( $user_id, 'telegram' );
	        $current_chat_id[]	= $result['chat_id'];
	        $current_chat_id	= array_unique( $current_chat_id );

	        if ( update_user_meta( $user_id, 'telegram', $current_chat_id ) ) {
	            $text = 'Добро пожаловать в WooCommerce.' . PHP_EOL;
	            $text .= 'На странице плагина Вы должны увидеть номер Вашего чата ' . $result['chat_id'] . PHP_EOL;
	            $text .= 'Спасибо!';
	            $this->send_message_to_telegram( $text, $result['chat_id'], $this->token );
	        } else {
	            //if ( $chat_id = get_user_meta( $user_id, 'telegram', true ) ) {
	            if ( in_array( $result['chat_id'], get_user_meta( $user_id, 'telegram', true ) ) ) {
	                $text = 'Вы уже зарегистрированы в WooCommerce.' . PHP_EOL;
	                $text .= 'Спасибо за то, что Вы с нами.';
	                $this->send_message_to_telegram( $text, $result['chat_id'], $this->token );
	            }
	        }
	    } catch ( Exception $e ) {
	        $logger->info( wc_print_r( $e->getMessage(), true ) );
	    }
	}

	private function parse_text( string $text ) {
	    $input = array();
	    parse_str( $text, $input );

	    $user_id	= empty( $input['key'] ) ? false : $input['key'];
	    $hash		= empty( $input['auth'] ) ? false : $input['auth'];

	    if ( $user_id and $hash and $hash == md5( 'wctelegram2020' . $user_id ) ) {
	        return $user_id;
	    }
	    throw new Exception( 'Не найден пользователь или не совпал секрет!' );
	}

	private function decode_post( string $post ): array {
	    $data		= json_decode( $post, true );
	    $text		= empty( $data['message']['text'] ) ? false : $data['message']['text'];
	    $text		= substr( $text, 1 );
	    $chat_id	= empty( $data['message']['chat']['id'] ) ? false : $data['message']['chat']['id'];
	    $callback	= empty( $data['callback_query'] ) ? false : $data['callback_query'];
	    
	    if ( $text and $chat_id ) {
	        return [
				'text'		=> $text,
				'chat_id'	=> $chat_id,
				'callback'	=> $callback,
	        ];
	    }
	    throw new Exception( 'Не хватает аргументов text или chat_id' );
	}

	public function send_message_to_telegram(
	  string $text,
	  string $chat_id,
	  string $token
	): void {
	    $url      = self::API_TELEGRAM . $token . '/sendMessage';

	    $keyboard = array( 'inline_keyboard' => array(
			array(
			    array( 'text' => 'Принять в обработку', 'callback_data' => 'key=order_process' )
			)
		));

	    $args     = [
			'timeout'		=> 5,
			'redirection'	=> 1,
			'httpversion' 	=> '1.0',
			'blocking'    	=> true,
			//'inline_keyboard'	=> true,
			'headers'     	=> [ 'Content-Type' => 'application/x-www-form-urlencoded' ],
			'body'        	=> [ 'text' => $text, 'chat_id' => $chat_id ],
	    ];

	    $response = wp_remote_post( $url, $args );
	    $logger   = wc_get_logger();
	    if ( is_wp_error( $response ) ) {
	        $error_message = $response->get_error_message();
	        $logger->info( wc_print_r( $error_message, true ) );
	    }
	}

	public function send_order_to_telegram( $order_id, $posted, $order ) {
		$text = ' Заказ № ' . $order->get_order_number() . ' с сайта ' . get_site_url() . PHP_EOL;
	    $text .= 'Клиент :' . $order->get_billing_first_name() . ' ' . $order->get_billing_last_name() . PHP_EOL;
	    $text .= 'Телефон :' . $order->get_billing_phone() . PHP_EOL;
	    $text .= 'Email :' . $order->get_billing_email() . PHP_EOL;
	    $text .= 'Сумма заказа :' . $order->get_total() . PHP_EOL;

	    $text  .= 'Содержимое заказа :' . PHP_EOL;
	    $items = $order->get_items();
		foreach ( $items as $item ) {
	        $product = $item->get_product();
	        $qty     = $item->get_quantity() ? $item->get_quantity() : 1;
	        $price   = wc_format_localized_price( $item->get_total() / $qty );
	        $text    .= 'Товар :' . $product->get_name() . ' Кол-во :' . $qty . ' Цена :' . $price;
	    }

	    foreach ( $this->get_telegram_users() as $user ) {
	        $chat_id = get_user_meta( $user->ID, 'telegram', true );
	        foreach ( $chat_id as $id ) {
	        	$this->send_message_to_telegram( $text, $id, $this->token );
	        }
	    }
	}

	private function get_telegram_users() {
	    return get_users([
	      'meta_key' => 'telegram',
	    ]);
	}

	public function validate_text_field( $key, $value ) {
	    if ( $key == 'token' ) {
	        if ( !$this->check_token( $value ) ) {
	            $this->add_error( 'Токен не существует' );
	        }
	    }
	    return parent::validate_text_field( $key, $value );
	}

	private function check_token( string $token ) {
	    $url      = self::API_TELEGRAM . $token . '/getMe';
	    $response = wp_remote_get( $url );
	    $body     = wp_remote_retrieve_body( $response );

	    if ( !empty( $body ) ) {
	        try {
	            $data = json_decode( $body, true );
	            if ( !empty( $data['result']['username'] ) ) {
	                return true;
	            }
	        } catch ( Exception $e ) {
	        	$logger->info( wc_print_r( $e->getMessage(), true ) );	
	        }
	    }
	    return false;
	}

	private function set_telegram_webhook() {
	    $logger = wc_get_logger();
	    $url    = self::API_TELEGRAM . $this->token . '/setWebhook';
	    $logger->info( wc_print_r( $url, true ) );
	    
	    $args   = [
			'timeout'     => 5,
			'redirection' => 1,
			'httpversion' => '1.0',
			'blocking'    => true,
			'headers'     => [ 'Content-Type' => 'application/x-www-form-urlencoded' ],
			'body'        => [ 'url' => home_url( '/?wc-api=woo-telegram' ) ],
	    ];
	    $response = wp_remote_post( $url, $args );

	    if ( is_wp_error( $response ) ) {
	        $error_message = $response->get_error_message();
	        $logger->info( wc_print_r( $error_message, true ) );
	    }
	}

	private function check_exists_webhook( string $token ) {
        $logger = wc_get_logger();
        $url    = self::API_TELEGRAM . $token . '/getWebhookInfo';
        $logger->info( wc_print_r( $url, true ) );

        $response = wp_remote_get( $url );
        $body     = wp_remote_retrieve_body( $response );
        if ( !empty( $body ) ) {
            try {
                $data = json_decode( $body, true );
                if ( !empty( $data['result']['url'] ) ) {
                    return true;
                }
            } catch ( Exception $e ) {
	        	$logger->info( wc_print_r( $e->getMessage(), true ) );
            }
        }
        return false;
    }
}

?>