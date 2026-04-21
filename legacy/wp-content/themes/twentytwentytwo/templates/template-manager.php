<?php
/**
 * The template for displaying the Manager app.
 *
 * Template name: Manager
 *
 */

//get_header();
?>
<html>

<head>
	<title>Менеджер заявок</title>
    </script>
</head>
<body>

<?php
// update
$ch = curl_init();
curl_setopt($ch, CURLOPT_URL, 'http://yiiiii.webtm.ru/web/optimistic-lock-rests/2');
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_CUSTOMREQUEST, 'PUT');
curl_setopt($ch, CURLOPT_POSTFIELDS, http_build_query(['done' => 0]));
$response = json_decode(curl_exec($ch), true);
curl_close($ch);
echo 'update response:<pre>'. print_r( $response, true ) . '</pre>';

// index
$ch = curl_init();
curl_setopt($ch, CURLOPT_URL, 'http://yiiiii.webtm.ru/web/optimistic-lock-rests');
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
$response = json_decode(curl_exec($ch), true);
curl_close($ch);
echo 'index response:<pre>'. print_r( $response, true ) . '</pre>';


?>

</body>

</html>