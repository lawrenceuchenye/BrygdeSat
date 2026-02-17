
%builtins output range_check poseidon

from starkware.cairo.common.serialize import serialize_word
from starkware.cairo.common.math import assert_not_zero
from starkware.cairo.common.cairo_builtins import PoseidonBuiltin

func main{
    output_ptr : felt*,
    range_check_ptr,
    poseidon_ptr : PoseidonBuiltin*
}(){
     
    alloc_locals;
    local prev_root;
    local new_root;

    %{
        # This hint tells Cairo to take data from the JSON input
        ids.prev_root = int(program_input['program_input'][0], 16)
        ids.new_root = int(program_input['program_input'][1], 16)
    %}

    // Output roots as public inputs
    serialize_word(prev_root);
    serialize_word(new_root);

    // Check new_root isn’t zero
    assert_not_zero(new_root);

    return ();
}

