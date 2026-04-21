<?php
/*
Plugin Name:  Mass ACF values setter
Description:  Choose pages and set values for their ACF fields
Version:      1.0
Author:       ozzy1986
Author URI:   https://profiles.wordpress.org/ozzy1986
*/

defined( 'ABSPATH' ) or die( 'No script kiddies please!' ); // blocking direct access

// add left menu item in admin that will contain all custom posts 
add_action( 'admin_menu', 'mass_acf_setter_menu' );
function mass_acf_setter_menu() {
	add_menu_page( 'ACF значения', 'ACF значения', 'edit_posts', 'mass-acf-setter', 'mass_acf_setter_options', 'dashicons-format-gallery', 5 );
}
function mass_acf_setter_options() {
	if ( !current_user_can( 'edit_posts' ) )  {
		wp_die( __( 'У Вас недостаточно прав, чтобы просматривать эту страницу.' ) );
	}

	?>
	<div class="wrap">
		<h1><?php _e( 'Выберите страницы и задайте значения для их кастомных полей' ); ?></h1>
	<?php


	// process submitted pages and acf field values
	$error = false;
	if ( $_POST['mass_acf_setter_submit'] ) {

		if ( ! wp_verify_nonce( $_POST['mass_acf_setter_settings_nonce'], 'mass_acf_setter_settings' ) ) {
			echo '<div class="error inline notice-warning notice-alt"><p>' . __( 'Несанкционированная попытка редактирования!' ) . '</p></div>';
			$error = true;
		}

		if ( empty( $_POST['check_pages'] ) ) {
			echo '<div class="error inline notice-warning notice-alt"><p>' . __( 'Выберите хотя бы одну страницу' ) . '</p></div>';
			$error = true;
		}
		

		if ( !$error ) {
			// remember checked pages and remove them from post array
			$check_pages = $_POST['check_pages'];
			unset( $_POST['check_pages'] );

			// remove other non acf fields values from post
			unset( $_POST['mass_acf_setter_settings_nonce'] );
			unset( $_POST['_wp_http_referer'] );
			unset( $_POST['mass_acf_setter_submit'] );

			foreach ( $check_pages as $page ) {
				$page = absint( $page );
				foreach ( $_POST as $selector => $value ) {
					if ( is_array( $value ) ) {
						// if it's a group instead of field then run through its fields
						foreach( $value as $key => $val ) {
							$result = update_sub_field( $key, $val, $page );
						}
					} else {
						// it is field, not group
						// get meta key by field key
						$real_selector = get_meta_key_by_field_key( $selector, $page );
						if ( $real_selector and $value ) {
							// if value is empty then ignore it
							$result = update_post_meta( $page, $real_selector, $value );
						}
					}
				}
			}

			echo '<div class="notice notice-success is-dismissible inline"><p>' . __( 'Поля заданы успешно!' ) . '</p></div>';
		}

	}


	// process field groups
	if ( $_POST['mass_acf_setter_save_groups'] ) {
		$checked_groups = array_map( 'absint', $_POST['check_field_groups']  ); // sanitize
		update_option( 'mass_acf_setter_field_groups', $checked_groups ); // save
	}


	// get pages
	$pages			= get_pages();

	// get field groups
	$field_groups	= acf_get_field_groups();
	$checked_groups	= get_option( 'mass_acf_setter_field_groups' );
	?>


		<h3><?php _e( 'Выберите группы полей для редактирования' ); ?></h3>	
		<form method="post" action="">
			<ul>
				<?php foreach ( $field_groups as $group ) { ?>
					<li><label>
						<input type="checkbox" name="check_field_groups[]" value="<?php echo $group['ID']; ?>" <?php echo @in_array( $group['ID'], $checked_groups ) ? 'checked="checked"' : ''; ?>>
						<?php echo $group['title']; ?>
					</label></li>
				<?php } ?>
			</ul>
			<br>
			<input type="submit" value="<?php _e( 'Обновить поля' ); ?>" name="mass_acf_setter_save_groups" class="button button-primary button-large">
		</form>
		<br><br><br><br>
	
		<form method="post" action="">
		<table style="width: 90%;">
			<tr>
				<th style="text-align: left; padding-bottom: 20px;"><?php _e( 'Страницы: ' ); ?></th>
				<th style="text-align: left; padding-bottom: 20px;"><?php _e( 'Поля: ' ); ?></th>
			</tr>

			<tr>
				
				<td style="width: 50%; vertical-align: top;"><table>
					
				<tr>
					<td>
						<input type="checkbox" name="check_all_pages" id="check_all_pages">
					</td>
					<td><label for="check_all_pages"><?php _e( 'Выбрать все страницы' ); ?></label></td>
				</tr>
				<tr><td colspan="2">&nbsp;</td></tr>
				<script type="text/javascript">
					jQuery(document).ready(function($) {
						$('#check_all_pages').on('click', function() {
							$('.check_pages').prop('checked', this.checked);
						});
					});
				</script>

				<?php foreach ( $pages as $page ) { ?>
					<tr>
						<td>
							<input type="checkbox" name="check_pages[]" class="check_pages" id="check_pages_<?php echo $page->ID; ?>" value="<?php echo $page->ID; ?>" <?php echo ( is_array( $check_pages ) and in_array( $page->ID, $check_pages ) ) ? 'checked="checked"' : ''; ?>>
						</td>
						<td><label for="check_pages_<?php echo $page->ID; ?>"><?php echo $page->post_title; ?></label></td>
					</tr>
				<?php } ?>
				</table></td>

				<td style="vertical-align: top;"><table style="width: 100%;">
				<?php 
				//echo '<br>field_groups<pre>' . print_r( $field_groups, true ) . '</pre>';
				foreach ( $field_groups as $group ) {
					if ( !in_array( $group['ID'], $checked_groups ) ) {
						continue;
					}

					echo '<tr><td colspan="2" style="padding-top: 10px; border-top: 1px solid grey; font-size: 14px;"><strong>' . $group['title'] . '</strong></td></tr>';

					$fields			= get_posts( array(
						'posts_per_page'			=> -1,
						'post_type'					=> 'acf-field',
						'orderby'					=> 'menu_order',
						'order'						=> 'ASC',
						'suppress_filters'			=> true, // DO NOT allow WPML to modify the query
						'post_parent'				=> $group['ID'],
						'post_status'				=> 'any',
						'update_post_meta_cache'	=> false
					));
					//echo '<br>fields<pre>' . print_r( $fields, true ) . '</pre>';
					foreach ( $fields as $field ) {
						$field_object = get_field_object( $field->post_name );
						if ( $field_object['type'] != 'group' ) { 
							?>
							<tr>
								<td><label><?php echo $field_object['label']; ?></label></td>
								<td><?php echo '<input type="' . $field_object['type'] . '" name="' . $field_object['key'] . '" value="' . @$_POST[ $field_object['key'] ] . '" style="width: 100%;">'; ?></td>
							</tr>
						<?php } else { ?>
							<tr><td colspan="2" style="padding-top: 10px;"><strong><?php echo $field_object['label']; ?></strong></td></tr>
							<?php foreach ( $field_object['sub_fields'] as $sub_field ) { ?>
								<tr>
									<td><label><?php echo $sub_field['label']; ?></label></td>
									<td><?php echo '<input type="' . $sub_field['type'] . '" name="' . $sub_field['key'] . '" value="' . @$_POST[ $sub_field['key'] ] . '" style="width: 100%;">'; ?></td>
								</tr>
							<?php } ?>
							<tr><td colspan="2" style="height: 10px;">&nbsp;</td></tr>
						<?php 
						}
						//echo '<br>$field_object<pre>' . print_r( $field_object, true ) . '</pre>';
						//echo '<br>$field<pre>' . print_r( $field, true ) . '</pre>';
						//echo '<br>unserialize<pre>' . print_r( unserialize( $field->post_content ), true ) . '</pre>';
					}
				}		
				?>
				</table></td>

			</tr>
			<tr>
				<td colspan="2" style="margin-top: 20px;">
				<?php echo wp_nonce_field( 'mass_acf_setter_settings', 'mass_acf_setter_settings_nonce', true, false ); ?>
				<input type="submit" value="<?php _e( 'Задать' ); ?>" name="mass_acf_setter_submit" class="button button-primary button-large">
				</td>
			</tr>
		</table>
		</form>
	
	
	</div>

	<?php
}


// to get post's meta key that relates to acf field key
function get_meta_key_by_field_key( $field_key, $post_id ) {
	$post_meta = get_post_meta( $post_id );
	
	// search for field key among values of meta
	foreach ( $post_meta as $meta_key => $meta_value ) {
		if ( $meta_value[0] == $field_key ) {
			// then related meta key should be the same key but without leading underscore "_"
			$real_meta_key = ltrim( $meta_key, '_' );
			// check if it exists
			if ( isset( $post_meta[ $real_meta_key ] ) ) {
				return $real_meta_key;
			}
		}
	}

	return false; // if nothing found
}
?>