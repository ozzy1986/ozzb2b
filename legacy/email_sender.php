<?php
error_reporting( E_ALL );
ini_set( 'display_errors', 1 );
	
session_start();

//echo 'POST<pre>' . print_r( $_POST, true ) . '</pre>';
//echo 'SERVER<pre>' . print_r( $_SERVER, true ) . '</pre>';
//echo 'SESSION<pre>' . print_r( $_SESSION, true ) . '</pre>';
//exit;

if ( empty( $_POST ) ) {
	exit( 'No data passed.' );
}

// define current site url
if ( isset( $_SERVER['HTTPS'] ) and $_SERVER['HTTPS'] != 'off' ) {
	$site_url = 'https://';
} else {
	$site_url = 'http://';
}
$site_url .= $_SERVER['SERVER_NAME'];

// check origin of request
if ( isset( $_SERVER['HTTP_ORIGIN'] ) ) {
    if ( $site_url != $_SERVER['HTTP_ORIGIN'] ) {
        exit( 'Invalid Origin header: ' . $_SERVER['HTTP_ORIGIN'] );
    }
} else {
    exit( 'No Origin header' );
}

// check referer
if ( isset( $_SERVER['HTTP_REFERER'] ) ) {
	$referer = parse_url( $_SERVER['HTTP_REFERER'] );
	$referer = $referer['scheme'] . '://' . $referer['host'];
    if ( $site_url != $referer ) {
        exit( 'Invalid referer: ' . $referer );
    }
} else {
    exit( 'No referer' );
}

// if it's a request for a token then generate it
if ( isset( $_POST['get_token'] ) ) {
	$token						= bin2hex( random_bytes( 32 ) );
	$_SESSION['email_token']	= $token;
	
	exit( 'token:' . $token );
}

// if it's a request for email then check a token
if ( empty( $_POST['get_token'] ) and !empty( $_POST['email_token'] ) ) {
	if ( $_POST['email_token'] != $_SESSION['email_token'] ) {
		exit( 'Tokens do not match.' );
	}
}

// check if recipient is specified
if ( empty( $_POST['to'] ) ) {
	exit( 'Recipient not set.' );
}
// if subject is specified
if ( empty( $_POST['subject'] ) ) {
	exit( 'Subject not set.' );
}
// if headers are specified
if ( empty( $_POST['headers'] ) ) {
	exit( 'Headers not set.' );
}
// if message is specified
if ( empty( $_POST['message'] ) ) {
	exit( 'Message not set.' );
}

$subject	= htmlspecialchars( $_POST['subject'], ENT_QUOTES, 'utf-8' );
$headers	= implode( "\r\n", $_POST['headers'] );
//$headers	.= "\r\n" . 'X-MSMail-Priority: High';
$headers	.= "\r\n" . 'X-Priority: 1';
$headers	.= "\r\n" . 'Priority: Urgent';
$headers	.= "\r\n" . 'Importance: high';
$headers	.= "\r\n" . 'X-Mailer: PHP' . phpversion();
$message	= $_POST['message'];

$error = false;
if ( is_array( $_POST['to'] ) ) {
	foreach ( $_POST['to'] as $to ) {
		$to			= htmlspecialchars( $to, ENT_QUOTES, 'utf-8' );
		$send_email	= mail( $to, $subject, $message, $headers );
	
		if ( !$send_email ) {
			echo 'error: ' . $to;
			$error = true;
		}
	}
	echo ( $error ) ? '' : 'success';
} else {
	$to			= htmlspecialchars( $_POST['to'], ENT_QUOTES, 'utf-8' );
	$send_email	= mail( $to, $subject, $message, $headers );
	
	echo ( $send_email ) ? 'success' : 'error';
}


exit;
?>