<?php

function ozz_get_post_id_by_url( $url = '' ) {
	$post_url	= trim( $url );
	$post_id	= url_to_postid( $post_url );

	if ( $post_id ) {
		return $post_id;
	} else {
		// try different approach assuming that only slug part was passed instead of full url
		$post = get_page_by_path( $post_url, ARRAY_A, ['post', 'page'] );
		if ( $post and $post['ID'] ) {
			return $post['ID'];
		} else {
			$post = get_page_by_path( untrailingslashit( $post_url ), ARRAY_A, ['post', 'page'] );
			if ( $post and $post['ID'] ) {
				return $post['ID'];
			} else {
				// nothing worked
				return false;
			}
		}
	}

	return false;
}

// Save user's changes
if ( !empty( $_POST['save'] ) and check_admin_referer( 'mass_tag_' . get_current_user_id() ) ) {
	//echo '<div>post<pre>' . print_r( $_FILES, true ) . '</pre></div>';
	
	$error			= false;

	$author			= intval( $_POST['author'] );
	$tag			= sanitize_text_field( $_POST['tag_name'] );
	$urls			= sanitize_textarea_field( $_POST['url_list'] );
	$url_list		= explode( PHP_EOL, $urls );
	
	// process file with list of urls if it was uploaded
	if ( !empty( $_FILES['url_list_file']['name'] ) ) {
		if ( !current_user_can( 'upload_files' ) and !empty( $_FILES['url_list_file'] ) ) {
			echo '<div class="error"><p>You are not allowed to upload files.</p></div>';
			$error = true;
		} else {
			// validate extension
			$file_info = wp_check_filetype( basename( $_FILES['url_list_file']['name'] ) );

			if ( $file_info['ext'] and in_array( $file_info['ext'] , ['txt', 'doc', 'docx'] ) ) {
				// if all ok read the file into array of urls
				$urls		= sanitize_textarea_field( file_get_contents( $_FILES['url_list_file']['tmp_name'] ) );
				$url_list	= explode( PHP_EOL, $urls ); // so list of urls from file overwrites same list from textarea
			} else {
				echo '<div class="error"><p>This file type is not allowed for upload.</p></div>';
				$error = true;
			}
		}
	}

	echo '<div style="display: none;"><pre>' . print_r( $url_list, true ) . '</pre></div>';

	$total_urls			= 0;
	$tagged_posts		= 0;
	$tagged_pages		= 0;
	$authored_posts		= 0;
	$failed_urls		= array();

	// attach the tag to each post from url list
	if ( $tag and !$error ) {
		foreach ( $url_list as $post_url ) {
			$total_urls++;
			$post_id	= ozz_get_post_id_by_url( $post_url );
			if ( $post_id ) {
				wp_set_post_tags( $post_id, $tag, true );
				if ( get_post_type( $post_id ) == 'page' ) {
					$tagged_pages++;
				} else {
					$tagged_posts++;
				}

				// change author of those posts if author was set
				if ( $author ) {
					$arg = array(
					    'ID'			=> $post_id,
					    'post_author'	=> $author
					);
					wp_update_post( $arg );
					$authored_posts++;
				}
			} else {
				$failed_urls[] = $post_url;
			}
		}
	}

}


// prepare list of authors
$authors = get_users( [ 'role__in' => [ 'author', 'subscriber', 'administrator', 'editor', 'shop_manager' ] ] );

?>
<div class="wrap">

<h1>Bulk Post Tagger</h1>

<?php
// output the result if any
if ( !empty( $_POST['save'] ) and check_admin_referer( 'mass_tag_' . get_current_user_id() ) ) {
	if ( $failed_urls ) {
		?>
		<script type="text/javascript">
			jQuery(document).ready(function($) {
				$('#show_failed_urls').on('click', function() {
					$('#failed_urls_block').toggle(200);
				});
			});
		</script>
		<table width="80%" cellspacing="10px">
		<tr><td style="min-width: 220px; vertical-align: top;">
			<?php
			echo '<div style="background-color: #f0f8f6; margin: 40px 0px 10px 0px; padding: 8px 10px; font-size: 20px; line-height: 30px;">Total urls: ' . $total_urls . '<br>Tagged posts: ' . $tagged_posts . '<br>Tagged pages: ' . $tagged_pages . '<br>Author changed: ' . $authored_posts . '</div>';
			?>
		</td><td style="vertical-align: top;">
			<div id="show_failed_urls" style="cursor: pointer; background-color: #f8f3f0; margin: 40px 0px 10px 0px; padding: 8px 10px; font-size: 20px; line-height: 30px; display: inline-block;">Failed post urls (<?php echo count( $failed_urls ); ?>): </div>
			<?php
			echo '<div id="failed_urls_block" style="display: none; background-color: #f8f8e7; margin: 40px 0px 10px 0px; padding: 8px 10px; font-size: 20px; line-height: 30px;">' . implode( '<br>', $failed_urls ) . '</div>';
			?>
		</td></tr>
		</table>
		<?php
	} else {
		echo '<div style="background-color: #f0f8f6; margin: 40px 0px 10px 0px; padding: 8px 10px; font-size: 20px; line-height: 30px;">Total urls: ' . $total_urls . '<br>Tagged posts: ' . $tagged_posts . '<br>Tagged pages: ' . $tagged_pages . '<br>Author changed: ' . $authored_posts . '</div>';
	}
}
?>


<form method="post" action="" enctype="multipart/form-data">
	<?php wp_nonce_field( 'mass_tag_' . get_current_user_id() ); ?>

	<table cellspacing="2" cellpadding="4" style="width: 600px;">
	<tr>
		<td><label for="tag_name">Tag name</label></td>
		<td><input type="text" name="tag_name" id="tag_name" style="width: 100%;" value="<?php echo @$tag; ?>"></td>
	</tr>
	<tr>
		<td><label for="tag_name">Author</label></td>
		<td>
			<select name="author">
				<option value="0">no change</option>
				<?php
				foreach ( $authors as $user ) {
					echo '<option value="' . $user->ID . '">' . $user->display_name . ' (' . $user->user_nicename . ')</option>';
				}
				?>
			</select>
		</td>
	</tr>
	<tr>
		<td><label for="url_list_file">Select file containing URLs of posts</label></td>
		<td><input name="url_list_file" id="url_list_file" type="file" style="width: 100%;"></td>
	</tr>
	<tr>
		<td><label for="url_list">Enter list of URLs of posts</label></td>
		<td><textarea name="url_list" id="url_list" rows="9" style="width: 100%;"><?php echo @$urls; ?></textarea></td>
	</tr>

	<tr>
		<td colspan="2"><input type="submit" name="save" class="button button-primary save alignleft" value="Tag now"></td>
	</tr>
	</table>
</form>

</div>