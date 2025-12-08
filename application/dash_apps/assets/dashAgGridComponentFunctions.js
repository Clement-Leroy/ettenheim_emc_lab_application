var dagcomponentfuncs = window.dashAgGridComponentFunctions = window.dashAgGridComponentFunctions || {};

dagcomponentfuncs.X_axis_options = function (params) {
    const items = params.data.x_axis_options;
    return {
        values: items,
    };
};

dagcomponentfuncs.Y_axis_options = function (params) {
    const items = params.data.y_axis_options;
    return {
        values: items,
    };
};

dagcomponentfuncs.Button = function (props) {
    const {setData, data} = props;

    function onClick() {
        setData();
    }
    return React.createElement(
        window.dash_bootstrap_components.Button,
        {
            onClick,
            className: props.className,
        },
        props.value
    );
};

dagcomponentfuncs.ButtonHeader = function (props) {
    function onClick() {
        newData = props.style
        dash_clientside.set_props("hide-button", {data: newData})
    }
    return React.createElement(
        window.dash_bootstrap_components.Button,
        {
            onClick,
            className: "block text-center text-md text-white rounded no-underline cursor-pointer hover:bg-blue-600 display: 'flex justifyContent: center alignItems': center",
			style: props.style,
        },
        props.displayName
    );
};

dagcomponentfuncs.EditButton = function (props) {
    const {setData, data} = props;

    function onClick() {
        setData();
    }

    return React.createElement(
        window.dash_bootstrap_components.Button,
        {
            onClick: onClick,
            children: "Edit",
            className: "block text-center text-md text-white rounded no-underline cursor-pointer hover:bg-blue-600 display: 'flex justifyContent: center alignItems': center",
        },
        props.value
    );
};
