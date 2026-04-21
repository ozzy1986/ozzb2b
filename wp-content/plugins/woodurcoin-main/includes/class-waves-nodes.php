<?php
/**
 * A class for receiving and processing information from the wavesnodes about transactions
 *
 * @since      1.0.0
 * @package    Woodurcoin
 * @subpackage Woodurcoin/includes
 * @author     granvik
 * @class      WavesNodes
 */

class WavesNodes
{
    private $assetDetailsSrc;
    private $transactionInfoSrc;

    public function __construct()
    {
        $this->assetDetailsSrc = "https://nodes.wavesnodes.com/assets/details/";
        $this->transactionInfoSrc = "https://nodes.wavesnodes.com/transactions/info/";
        $this->addressTransactionsSrc = "https://nodes.wavesnodes.com/transactions/address/";
        $this->addressValidateSrc = "https://nodes.wavesnodes.com/addresses/validate/";
    }

    private function get($url)
    {
        $response = wp_remote_get($url);
        $result = wp_remote_retrieve_body($response);
        return json_decode($result);
    }

    public function getTransactionInfo($id)
    {
        return $this->get($this->transactionInfoSrc . $id);
    }

    public function validAccount($address)
    {
        $result = $this->get($this->addressValidateSrc . $address);
        return $result->valid;
    }

    function findByAttachment($attachment)
    {
        $result = $this->get($this->addressTransactionsSrc . $this->address . '/limit/50');
        if ($result) {
            $result_encoded = json_encode($result);
            $resultarray = json_decode($result_encoded, true);

            foreach ($resultarray as $payments) {
                foreach ($payments as $payment) {
                    if ($payment['attachment'] == $attachment) {
                        return array(
                            'result' => true,
                            'id' => $payment['id'],
                            'amount' => $payment['amount'],
                        );
                    }
                }
            }
            return array(
                'result' => false,
            );
        } else {
            return array(
                'result' => false,
            );
        }
    }
}