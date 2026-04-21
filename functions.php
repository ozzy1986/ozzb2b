<?php

ini_set('display_errors', '1');
ini_set('display_startup_errors', '1');
error_reporting(E_ALL);

$site_url = 'https://youcamp.pro/price_bidder_old/';


// curl request
function curl_request($url='', $method='', $data='', $headers='', $debug=false) {
	// validate and sanitize fields
	if (empty($url)) {
		return false;
	}
	if (empty($data)) {
		$data = [];
	}
	if (empty($method)) {
		$method = 'GET';
	} else {
		$method = strtoupper($method);
	}
	if ($method == 'GET') {
		if (strpos($url, '?') === false) {
			$url .= '?'.http_build_query( $data );
		} else {
			$url .= '&'.http_build_query( $data );
		}
	}

	// init curl
	$ch = curl_init($url);
	curl_setopt($ch, CURLOPT_CUSTOMREQUEST, $method);
	// curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data, JSON_UNESCAPED_UNICODE));
	// curl_setopt($ch, CURLOPT_POSTFIELDS, http_build_query( $data ));
	curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
	curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
	curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, false);
	curl_setopt($ch, CURLOPT_HEADER, false);

	if (!empty($headers)) {
		curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
	}

	if (is_array($data)) {
		$data = http_build_query($data);
	}

	switch ( $method ) {
		case 'POST':
			curl_setopt( $ch, CURLOPT_POST, true );
			curl_setopt( $ch, CURLOPT_POSTFIELDS, $data );
			break;
		case 'PUT':
			curl_setopt( $ch, CURLOPT_CUSTOMREQUEST, 'PUT' );
			curl_setopt( $ch, CURLOPT_POSTFIELDS, $data );
			break;
		case 'DELETE':
			curl_setopt( $ch, CURLOPT_CUSTOMREQUEST, 'DELETE' );
			curl_setopt( $ch, CURLOPT_POSTFIELDS, $data );
			break;
		default:
			curl_setopt( $ch, CURLOPT_POST, true );
			curl_setopt( $ch, CURLOPT_POSTFIELDS, $data );
			break;
	}
	$result	= curl_exec($ch);
	$info	= curl_getinfo($ch);
	curl_close($ch);
	
	if (!empty($result) and $result != 'null') {
		$result = json_decode($result, true);
	}

	if ($debug) {
		echo '<br>url:<pre>'.print_r($url, true).'</pre>';
		echo '<br>headers:<pre>'.print_r($headers, true).'</pre>';
		echo '<br>data:<pre>'.print_r($data, true).'</pre>';
		echo '<br>info:<pre>'.print_r($info, true).'</pre>';
	}

	return $result;
}

// generate JWT token from
function create_jwt($data, $secret = '') {
	if (empty($secret)) {
		$secret = 'youcamp';
	}
	
	$header = [
		'alg' => 'HS512', 
		'typ' => 'JWT' 
	];
	$header = base64_url_encode(json_encode($header));
	
	$payload = $data;
	$payload = base64_url_encode(json_encode($payload));
	
	$signature = base64_url_encode(hash_hmac('sha512', $header.'.'.$payload, $secret, true));
	
	$jwt = "$header.$payload.$signature";

	return $jwt;    
}

function is_valid_jwt($token, $secret='') {
	if (empty($secret)) {
		$secret = 'test';
	}

	// Separate the "Bearer" keyword and the token
	$token_parts = explode(' ', $token);

	// Check if the token exists and is well-formatted
	if (count($token_parts) != 2 || $token_parts[0] != 'Bearer') {
		// echo json_encode([
		// 	'result'		=> 'debug',
		// 	'token_parts'	=> $token_parts
		// ]);
		// exit;
		return false;
	}

	// Extract the actual token
	$jwt_token = $token_parts[1];

	$jwt_parts = explode('.', $jwt_token);

	$signature_provided = $jwt_parts[2];

	$signature = hash_hmac('sha512', $jwt_parts[0].'.'.$jwt_parts[1], $secret, true);
	$signature = base64_url_encode($signature);

	// Verify the signature of the token with your secret key
	if ($signature === $signature_provided) {
		return true;
	} else {
		return false;
	}
}

/**
 * per https://stackoverflow.com/questions/2040240/php-function-to-generate-v4-uuid/15875555#15875555
 */
function base64_url_encode($text):String{
	return str_replace(['+', '/', '='], ['-', '_', ''], base64_encode($text));
}

// returns correct form of word for given number
function plural_form($number, $one, $four, $many) {
	if ($number > 4 and $number < 21) {
		return $many;
	}

	$number = $number % 10;
	if ($number == 0) {
		return $many;
	} else if ($number == 1) {
		return $one;
	} else if ( $number < 5) {
		return $four;
	} else {
		return $many;
	}
}

// validate uploaded file
function validate_upload($file_array) {
	// Undefined | Multiple Files | $_FILES Corruption Attack
    // If this request falls under any of them, treat it invalid.
    if (
        !isset($file_array['error']) ||
        is_array($file_array['error'])
    ) {
        throw new RuntimeException('Invalid parameters.');
    }

    // Check $file_array['error'] value.
    switch ($file_array['error']) {
        case UPLOAD_ERR_OK:
            break;
        case UPLOAD_ERR_NO_FILE:
            throw new RuntimeException('No file sent.');
        case UPLOAD_ERR_INI_SIZE:
        case UPLOAD_ERR_FORM_SIZE:
            throw new RuntimeException('Exceeded filesize limit.');
        default:
            throw new RuntimeException('Unknown errors.');
    }

    // You should also check filesize here. 
    if ($file_array['size'] > 1000000) {
        throw new RuntimeException('Exceeded filesize limit.');
    }

    // DO NOT TRUST $file_array['mime'] VALUE !!
    // Check MIME Type by yourself.
    $finfo = new finfo(FILEINFO_MIME_TYPE);
	// echo '<br>file format:<pre>'.print_r($finfo->file($file_array['tmp_name']), true).'</pre><br>';
    if (false === $ext = array_search(
        $finfo->file($file_array['tmp_name']),
        ['text/plain', 'text/csv'],
        true
    )) {
        throw new RuntimeException('Invalid file format.');
    }

    return true;
}