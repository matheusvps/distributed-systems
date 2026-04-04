const config = require("../../config");

function isPromotionValid(promo) {
  const validCategories = config.categories || [];
  return (
    promo &&
    typeof promo.id === "string" &&
    promo.id.trim().length > 0 &&
    typeof promo.title === "string" &&
    promo.title.trim().length > 0 &&
    typeof promo.category === "string" &&
    validCategories.includes(promo.category) &&
    typeof promo.store === "string" &&
    promo.store.trim().length > 0 &&
    Number.isFinite(promo.price) &&
    promo.price > 0
  );
}

function isVoteValid(payload) {
  return (
    payload &&
    typeof payload.promotionId === "string" &&
    payload.promotionId.trim().length > 0 &&
    [1, -1].includes(payload.vote)
  );
}

module.exports = {
  isPromotionValid,
  isVoteValid
};
