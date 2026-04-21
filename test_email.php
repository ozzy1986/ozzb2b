<html>
<head>
	<script src="https://ajax.googleapis.com/ajax/libs/jquery/2.1.3/jquery.min.js"></script>
	<script type="text/javascript">
	jQuery(document).ready(function($){
		$('#send').on('click', function() {
			$.ajax({
				type: 'POST',
				url: 'email_sender.php',
				data: {'get_token': 13}, // first request a token
				success: function(response) {
					console.log('response', response);
					
					if (response.includes('token:')) {
						let start = response.indexOf(':') + 1;
						let token = response.substring(start);
						console.log(start, token);
						
						// now that we have token let's request email sending
						$.ajax({
							type: 'POST',
							url: 'email_sender.php',
							data: {
								'email_token': token,
								'to': ['ozeritski@gmail.com','ozeritski2@gmail.com'],
								'subject': 'Simple email check',
								'headers': ['From: Kirill < ozeritski2@gmail.com >', 'Content-Type: text/html; charset=utf-8', 'MIME-Version: 1.0', 'Reply-To: no-reply@gmail.com'],
								'message': `
									<h1>Hello!</h1>
									<h2>world</h2>
									
									<div>This is message</div>
								`
							}, 
							success: function(email_response) {
								console.log('email_response', email_response);
								
								if (email_response == 'success') {
									alert('Email sent successfully!');
								}
							}
						});
					}
				}
			});
		});
	});
	</script>
</head>
<body>
	<button id="send">Send email</button>
</body>
</html>